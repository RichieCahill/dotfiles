"""Submit an OpenAI Batch API bill-summarization job over compressed text.

Reads the first N bills from a CSV with a `text_content` column, compresses
each via `bill_token_compression.compress_bill_text`, builds a JSONL file of
summarization requests, and submits it as an asynchronous Batch API job
against `/v1/chat/completions`. Also writes a CSV of per-bill pre/post-
compression token counts.
"""

from __future__ import annotations

import csv
import json
import logging
import re
import sys
from os import getenv
from pathlib import Path
from typing import Annotated

import httpx
import typer
from tiktoken import Encoding, get_encoding

from python.prompt_bench.bill_token_compression import compress_bill_text
from python.prompt_bench.summarization_prompts import SUMMARIZATION_SYSTEM_PROMPT, SUMMARIZATION_USER_TEMPLATE

logger = logging.getLogger(__name__)

OPENAI_API_BASE = "https://api.openai.com/v1"


def load_bills(csv_path: Path, count: int = 0) -> list[tuple[str, str]]:
    """Return (bill_id, text_content) tuples with non-empty text.

    If `count` is 0 or negative, all rows are returned.
    """
    csv.field_size_limit(sys.maxsize)
    bills: list[tuple[str, str]] = []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            text_content = (row.get("text_content") or "").strip()
            if not text_content:
                continue
            bill_id = row.get("bill_id") or row.get("id") or f"row-{len(bills)}"
            version_code = row.get("version_code") or ""
            unique_id = f"{bill_id}-{version_code}" if version_code else bill_id
            bills.append((unique_id, text_content))
            if count > 0 and len(bills) >= count:
                break
    return bills


def safe_filename(value: str) -> str:
    """Make a string safe for use as a filename or batch custom_id."""
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_") or "unnamed"


def build_request(custom_id: str, model: str, bill_text: str) -> dict:
    """Build one OpenAI batch request line."""
    return {
        "custom_id": custom_id,
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {
            "model": model,
            "messages": [
                {"role": "system", "content": SUMMARIZATION_SYSTEM_PROMPT},
                {"role": "user", "content": SUMMARIZATION_USER_TEMPLATE.format(text_content=bill_text)},
            ],
        },
    }


def write_jsonl(path: Path, lines: list[dict]) -> None:
    """Write a list of dicts as JSONL."""
    with path.open("w", encoding="utf-8") as handle:
        for line in lines:
            handle.write(json.dumps(line, ensure_ascii=False))
            handle.write("\n")


def upload_file(client: httpx.Client, path: Path) -> str:
    """Upload a JSONL file to the OpenAI Files API and return its file id."""
    with path.open("rb") as handle:
        response = client.post(
            f"{OPENAI_API_BASE}/files",
            files={"file": (path.name, handle, "application/jsonl")},
            data={"purpose": "batch"},
        )
    response.raise_for_status()
    return response.json()["id"]


def prepare_requests(
    bills: list[tuple[str, str]],
    *,
    model: str,
    encoder: Encoding,
) -> tuple[list[dict], list[dict]]:
    """Build (request_lines, token_rows) from bills.

    Each bill is compressed before being turned into a request line.
    Each `token_rows` entry has chars + token counts for one bill so the caller
    can write a per-bill CSV.
    """
    request_lines: list[dict] = []
    token_rows: list[dict] = []
    for bill_id, text_content in bills:
        raw_token_count = len(encoder.encode(text_content))
        compressed_text = compress_bill_text(text_content)
        compressed_token_count = len(encoder.encode(compressed_text))
        token_rows.append(
            {
                "bill_id": bill_id,
                "raw_chars": len(text_content),
                "compressed_chars": len(compressed_text),
                "raw_tokens": raw_token_count,
                "compressed_tokens": compressed_token_count,
                "token_ratio": (compressed_token_count / raw_token_count) if raw_token_count else None,
            },
        )
        safe_id = safe_filename(bill_id)
        request_lines.append(build_request(safe_id, model, compressed_text))
    return request_lines, token_rows


def write_token_csv(path: Path, token_rows: list[dict]) -> tuple[int, int]:
    """Write per-bill token counts to CSV. Returns (raw_total, compressed_total)."""
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["bill_id", "raw_chars", "compressed_chars", "raw_tokens", "compressed_tokens", "token_ratio"],
        )
        writer.writeheader()
        writer.writerows(token_rows)
    raw_total = sum(row["raw_tokens"] for row in token_rows)
    compressed_total = sum(row["compressed_tokens"] for row in token_rows)
    return raw_total, compressed_total


def create_batch(client: httpx.Client, input_file_id: str, description: str) -> dict:
    """Create a batch job and return its full response payload."""
    response = client.post(
        f"{OPENAI_API_BASE}/batches",
        json={
            "input_file_id": input_file_id,
            "endpoint": "/v1/chat/completions",
            "completion_window": "24h",
            "metadata": {"description": description},
        },
    )
    response.raise_for_status()
    return response.json()


def main(
    csv_path: Annotated[Path, typer.Option("--csv", help="Bills CSV path")] = Path("bills.csv"),
    output_dir: Annotated[Path, typer.Option("--output-dir", help="Where to write JSONL + metadata")] = Path(
        "output/openai_batch",
    ),
    model: Annotated[str, typer.Option(help="OpenAI model id")] = "gpt-5-mini",
    count: Annotated[int, typer.Option(help="Max bills to process, 0 = all")] = 0,
    log_level: Annotated[str, typer.Option(help="Log level")] = "INFO",
) -> None:
    """Submit an OpenAI Batch job of compressed bill summaries."""
    logging.basicConfig(level=log_level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    api_key = getenv("CLOSEDAI_TOKEN") or getenv("OPENAI_API_KEY")
    if not api_key:
        message = "Neither CLOSEDAI_TOKEN nor OPENAI_API_KEY is set"
        raise typer.BadParameter(message)
    if not csv_path.is_file():
        message = f"CSV not found: {csv_path}"
        raise typer.BadParameter(message)

    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Loading %d bills from %s", count, csv_path)
    bills = load_bills(csv_path, count)
    if len(bills) < count:
        logger.warning("Only %d bills available (requested %d)", len(bills), count)

    encoder = get_encoding("o200k_base")
    request_lines, token_rows = prepare_requests(bills, model=model, encoder=encoder)

    token_csv_path = output_dir / "token_counts.csv"
    raw_tokens_total, compressed_tokens_total = write_token_csv(token_csv_path, token_rows)
    logger.info(
        "Token counts: raw=%d compressed=%d ratio=%.3f -> %s",
        raw_tokens_total,
        compressed_tokens_total,
        (compressed_tokens_total / raw_tokens_total) if raw_tokens_total else 0.0,
        token_csv_path,
    )

    jsonl_path = output_dir / "requests.jsonl"
    write_jsonl(jsonl_path, request_lines)
    logger.info("Wrote %s (%d bills)", jsonl_path, len(request_lines))

    headers = {"Authorization": f"Bearer {api_key}"}
    with httpx.Client(headers=headers, timeout=httpx.Timeout(300.0)) as client:
        logger.info("Uploading JSONL")
        file_id = upload_file(client, jsonl_path)
        logger.info("Uploaded: %s", file_id)

        logger.info("Creating batch")
        batch = create_batch(client, file_id, f"compressed bill summaries x{len(request_lines)} ({model})")
        logger.info("Batch created: %s", batch["id"])

    metadata = {
        "model": model,
        "count": len(bills),
        "jsonl": str(jsonl_path),
        "input_file_id": file_id,
        "batch_id": batch["id"],
        "raw_tokens_total": raw_tokens_total,
        "compressed_tokens_total": compressed_tokens_total,
        "batch": batch,
    }
    metadata_path = output_dir / "batch.json"
    metadata_path.write_text(json.dumps(metadata, indent=2))
    logger.info("Wrote metadata to %s", metadata_path)


def cli() -> None:
    """Typer entry point."""
    typer.run(main)


if __name__ == "__main__":
    cli()

"""Run two interactive OpenAI chat-completion sweeps over bill text.

Reads the first N bills from a CSV with a `text_content` column and sends two
sweeps through `/v1/chat/completions` concurrently — one with the raw bill
text, one with the compressed bill text. Each request's prompt is saved to
disk alongside the OpenAI response id so the prompts and responses can be
correlated later.
"""

from __future__ import annotations

import csv
import json
import logging
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from os import getenv
from pathlib import Path
from typing import Annotated

import httpx
import typer

from python.prompt_bench.bill_token_compression import compress_bill_text
from python.prompt_bench.summarization_prompts import SUMMARIZATION_SYSTEM_PROMPT, SUMMARIZATION_USER_TEMPLATE

logger = logging.getLogger(__name__)

OPENAI_API_BASE = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-5.4-mini"
DEFAULT_COUNT = 100
SEED = 42


def load_bills(csv_path: Path, count: int) -> list[tuple[str, str]]:
    """Return up to `count` (bill_id, text_content) tuples with non-empty text."""
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
            if len(bills) >= count:
                break
    return bills


def build_messages(bill_text: str) -> list[dict]:
    """Return the system + user message pair for a bill."""
    return [
        {"role": "system", "content": SUMMARIZATION_SYSTEM_PROMPT},
        {"role": "user", "content": SUMMARIZATION_USER_TEMPLATE.format(text_content=bill_text)},
    ]


def safe_filename(value: str) -> str:
    """Make a string safe for use as a filename."""
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_") or "unnamed"


def run_one_request(
    client: httpx.Client,
    *,
    bill_id: str,
    label: str,
    bill_text: str,
    model: str,
    output_path: Path,
) -> tuple[bool, float, str | None]:
    """Send one chat-completion request and persist prompt + response.

    Returns (success, elapsed_seconds, response_id).
    """
    messages = build_messages(bill_text)
    payload = {
        "model": model,
        "messages": messages,
        "seed": SEED,
    }
    start = time.monotonic()
    record: dict = {
        "bill_id": bill_id,
        "label": label,
        "model": model,
        "seed": SEED,
        "input_chars": len(bill_text),
        "messages": messages,
    }
    try:
        response = client.post(f"{OPENAI_API_BASE}/chat/completions", json=payload)
        response.raise_for_status()
        body = response.json()
    except httpx.HTTPStatusError as error:
        elapsed = time.monotonic() - start
        record["error"] = {
            "status_code": error.response.status_code,
            "body": error.response.text,
            "elapsed_seconds": elapsed,
        }
        output_path.write_text(json.dumps(record, ensure_ascii=False, indent=2))
        logger.exception("HTTP error for %s/%s after %.2fs", label, bill_id, elapsed)
        return False, elapsed, None
    except Exception as error:
        elapsed = time.monotonic() - start
        record["error"] = {"message": str(error), "elapsed_seconds": elapsed}
        output_path.write_text(json.dumps(record, ensure_ascii=False, indent=2))
        logger.exception("Failed: %s/%s after %.2fs", label, bill_id, elapsed)
        return False, elapsed, None

    elapsed = time.monotonic() - start
    response_id = body.get("id")
    record["response_id"] = response_id
    record["elapsed_seconds"] = elapsed
    record["usage"] = body.get("usage")
    record["response"] = body
    output_path.write_text(json.dumps(record, ensure_ascii=False, indent=2))
    logger.info("Done: %s/%s id=%s in %.2fs", label, bill_id, response_id, elapsed)
    return True, elapsed, response_id


def main(
    csv_path: Annotated[Path, typer.Option("--csv", help="Bills CSV path")] = Path("bills.csv"),
    output_dir: Annotated[Path, typer.Option("--output-dir", help="Where to write per-request JSON")] = Path(
        "output/openai_runs",
    ),
    model: Annotated[str, typer.Option(help="OpenAI model id")] = DEFAULT_MODEL,
    count: Annotated[int, typer.Option(help="Number of bills per set")] = DEFAULT_COUNT,
    concurrency: Annotated[int, typer.Option(help="Concurrent in-flight requests")] = 16,
    log_level: Annotated[str, typer.Option(help="Log level")] = "INFO",
) -> None:
    """Run two interactive OpenAI sweeps (compressed + uncompressed) over bill text."""
    logging.basicConfig(level=log_level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    api_key = getenv("CLOSEDAI_TOKEN") or getenv("OPENAI_API_KEY")
    if not api_key:
        message = "Neither CLOSEDAI_TOKEN nor OPENAI_API_KEY is set"
        raise typer.BadParameter(message)
    if not csv_path.is_file():
        message = f"CSV not found: {csv_path}"
        raise typer.BadParameter(message)

    compressed_dir = output_dir / "compressed"
    uncompressed_dir = output_dir / "uncompressed"
    compressed_dir.mkdir(parents=True, exist_ok=True)
    uncompressed_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Loading %d bills from %s", count, csv_path)
    bills = load_bills(csv_path, count)
    if len(bills) < count:
        logger.warning("Only %d bills available (requested %d)", len(bills), count)

    tasks: list[tuple[str, str, str, Path]] = []
    for bill_id, text_content in bills:
        filename = f"{safe_filename(bill_id)}.json"
        tasks.append((bill_id, "compressed", compress_bill_text(text_content), compressed_dir / filename))
        tasks.append((bill_id, "uncompressed", text_content, uncompressed_dir / filename))

    logger.info("Submitting %d requests at concurrency=%d", len(tasks), concurrency)

    headers = {"Authorization": f"Bearer {api_key}"}
    completed = 0
    failed = 0
    index: list[dict] = []
    wall_start = time.monotonic()
    with (
        httpx.Client(headers=headers, timeout=httpx.Timeout(300.0)) as client,
        ThreadPoolExecutor(
            max_workers=concurrency,
        ) as executor,
    ):
        future_to_task = {
            executor.submit(
                run_one_request,
                client,
                bill_id=bill_id,
                label=label,
                bill_text=bill_text,
                model=model,
                output_path=output_path,
            ): (bill_id, label, output_path)
            for bill_id, label, bill_text, output_path in tasks
        }
        for future in as_completed(future_to_task):
            bill_id, label, output_path = future_to_task[future]
            success, elapsed, response_id = future.result()
            if success:
                completed += 1
            else:
                failed += 1
            index.append(
                {
                    "bill_id": bill_id,
                    "label": label,
                    "response_id": response_id,
                    "elapsed_seconds": elapsed,
                    "success": success,
                    "path": str(output_path),
                },
            )
    wall_elapsed = time.monotonic() - wall_start

    summary = {
        "model": model,
        "count": len(bills),
        "completed": completed,
        "failed": failed,
        "wall_seconds": wall_elapsed,
        "concurrency": concurrency,
        "results": index,
    }
    summary_path = output_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2))
    logger.info(
        "Done: completed=%d failed=%d wall=%.1fs summary=%s",
        completed,
        failed,
        wall_elapsed,
        summary_path,
    )


def cli() -> None:
    """Typer entry point."""
    typer.run(main)


if __name__ == "__main__":
    cli()

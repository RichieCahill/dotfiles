"""Build a fine-tuning JSONL dataset from batch request + output files.

Joins the original request JSONL (system + user messages) with the batch
output JSONL (assistant completions) by custom_id to produce a ChatML-style
messages JSONL suitable for fine-tuning.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Annotated

import typer

logger = logging.getLogger(__name__)

HTTP_OK = 200


def load_requests(path: Path) -> dict[str, list[dict]]:
    """Parse request JSONL into {custom_id: messages}."""
    results: dict[str, list[dict]] = {}
    with path.open(encoding="utf-8") as handle:
        for raw_line in handle:
            stripped = raw_line.strip()
            if not stripped:
                continue
            record = json.loads(stripped)
            custom_id = record["custom_id"]
            messages = record["body"]["messages"]
            results[custom_id] = messages
    return results


def load_completions(path: Path) -> dict[str, str]:
    """Parse batch output JSONL into {custom_id: assistant_content}."""
    results: dict[str, str] = {}
    with path.open(encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, 1):
            stripped = raw_line.strip()
            if not stripped:
                continue
            record = json.loads(stripped)
            custom_id = record["custom_id"]
            response = record.get("response", {})
            if response.get("status_code") != HTTP_OK:
                logger.warning("Skipping %s (line %d): status %s", custom_id, line_number, response.get("status_code"))
                continue
            body = response.get("body", {})
            choices = body.get("choices", [])
            if not choices:
                logger.warning("Skipping %s (line %d): no choices", custom_id, line_number)
                continue
            content = choices[0].get("message", {}).get("content", "")
            if not content:
                logger.warning("Skipping %s (line %d): empty content", custom_id, line_number)
                continue
            results[custom_id] = content
    return results


def main(
    requests_path: Annotated[Path, typer.Option("--requests", help="Batch request JSONL")] = Path(
        "output/openai_batch/requests.jsonl",
    ),
    batch_output: Annotated[Path, typer.Option("--batch-output", help="Batch output JSONL")] = Path(
        "batch_69d84558d91c819091d53f08d78f9fd6_output.jsonl",
    ),
    output_path: Annotated[Path, typer.Option("--output", help="Fine-tuning JSONL output")] = Path(
        "output/finetune_dataset.jsonl",
    ),
    log_level: Annotated[str, typer.Option(help="Log level")] = "INFO",
) -> None:
    """Build fine-tuning dataset by joining request and output JSONL files."""
    logging.basicConfig(level=log_level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    logger.info("Loading requests from %s", requests_path)
    requests = load_requests(requests_path)
    logger.info("Loaded %d requests", len(requests))

    logger.info("Loading completions from %s", batch_output)
    completions = load_completions(batch_output)
    logger.info("Loaded %d completions", len(completions))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    matched = 0
    skipped = 0

    with output_path.open("w", encoding="utf-8") as handle:
        for custom_id, messages in requests.items():
            assistant_content = completions.get(custom_id)
            if assistant_content is None:
                skipped += 1
                continue

            example = {
                "messages": [*messages, {"role": "assistant", "content": assistant_content}],
            }
            handle.write(json.dumps(example, ensure_ascii=False))
            handle.write("\n")
            matched += 1

    logger.info("Wrote %d examples to %s (skipped %d unmatched)", matched, output_path, skipped)


def cli() -> None:
    """Typer entry point."""
    typer.run(main)


if __name__ == "__main__":
    cli()

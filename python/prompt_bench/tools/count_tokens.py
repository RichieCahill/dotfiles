"""Sum token usage across compressed and uncompressed run directories."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Annotated

import typer

logger = logging.getLogger(__name__)


@dataclass
class UsageTotals:
    """Aggregate usage counters for a directory of run records."""

    files: int = 0
    errors: int = 0
    prompt_tokens: int = 0
    cached_tokens: int = 0
    completion_tokens: int = 0
    reasoning_tokens: int = 0
    total_tokens: int = 0
    per_file: list[tuple[str, int, int, int]] = field(default_factory=list)


def tally_directory(directory: Path) -> UsageTotals:
    """Return aggregated usage stats for every JSON record in a directory."""
    totals = UsageTotals()
    decoder = json.JSONDecoder()
    for path in sorted(directory.glob("*.json")):
        text = path.read_text().lstrip()
        record, _ = decoder.raw_decode(text)
        totals.files += 1
        usage = record.get("usage")
        if not usage:
            totals.errors += 1
            continue
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", 0)
        cached_tokens = (usage.get("prompt_tokens_details") or {}).get("cached_tokens", 0)
        reasoning_tokens = (usage.get("completion_tokens_details") or {}).get("reasoning_tokens", 0)
        totals.prompt_tokens += prompt_tokens
        totals.completion_tokens += completion_tokens
        totals.total_tokens += total_tokens
        totals.cached_tokens += cached_tokens
        totals.reasoning_tokens += reasoning_tokens
        totals.per_file.append((path.name, prompt_tokens, completion_tokens, total_tokens))
    return totals


def log_totals(label: str, totals: UsageTotals) -> None:
    """Log a one-block summary for a directory."""
    counted = totals.files - totals.errors
    average_total = totals.total_tokens / counted if counted else 0
    logger.info("[%s]", label)
    logger.info("  files          : %d (with usage: %d, errors: %d)", totals.files, counted, totals.errors)
    logger.info("  prompt tokens  : %d", totals.prompt_tokens)
    logger.info("  cached tokens  : %d", totals.cached_tokens)
    logger.info("  completion tok : %d", totals.completion_tokens)
    logger.info("  reasoning tok  : %d", totals.reasoning_tokens)
    logger.info("  total tokens   : %d", totals.total_tokens)
    logger.info("  avg total/file : %.1f", average_total)


def main(
    runs_dir: Annotated[Path, typer.Option("--runs-dir")] = Path("output/openai_runs_temp_1"),
    log_level: Annotated[str, typer.Option("--log-level")] = "INFO",
) -> None:
    """Print token usage totals for the compressed and uncompressed run directories."""
    logging.basicConfig(level=log_level, format="%(message)s")

    grand = UsageTotals()
    for label in ("compressed", "uncompressed"):
        directory = runs_dir / label
        if not directory.is_dir():
            logger.warning("%s: directory not found at %s", label, directory)
            continue
        totals = tally_directory(directory)
        log_totals(label, totals)
        grand.files += totals.files
        grand.errors += totals.errors
        grand.prompt_tokens += totals.prompt_tokens
        grand.cached_tokens += totals.cached_tokens
        grand.completion_tokens += totals.completion_tokens
        grand.reasoning_tokens += totals.reasoning_tokens
        grand.total_tokens += totals.total_tokens

    log_totals("grand total", grand)


if __name__ == "__main__":
    typer.run(main)

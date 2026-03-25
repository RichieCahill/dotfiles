"""Ingestion pipeline for loading JSONL post files into the weekly-partitioned posts table.

Usage:
    ingest-posts /path/to/files/
    ingest-posts /path/to/single_file.jsonl
    ingest-posts /data/dir/ --workers 4 --batch-size 5000
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

import typer
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from python.orm.common import get_postgres_engine
from python.orm.data_science_dev.posts.failed_ingestion import FailedIngestion
from python.orm.data_science_dev.posts.tables import Posts
from python.parallelize import parallelize_process

if TYPE_CHECKING:
    from collections.abc import Iterator

logger = logging.getLogger(__name__)


app = typer.Typer(help="Ingest JSONL post files into the partitioned posts table.")


@app.command()
def main(
    path: Annotated[Path, typer.Argument(help="Directory containing JSONL files, or a single JSONL file")],
    batch_size: Annotated[int, typer.Option(help="Rows per INSERT batch")] = 10000,
    workers: Annotated[int, typer.Option(help="Parallel workers for multi-file ingestion")] = 4,
    pattern: Annotated[str, typer.Option(help="Glob pattern for JSONL files")] = "*.jsonl",
) -> None:
    """Ingest JSONL post files into the weekly-partitioned posts table."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )

    if path.is_file():
        ingest_file(str(path), batch_size=batch_size)
    elif path.is_dir():
        ingest_directory(path, batch_size=batch_size, max_workers=workers, pattern=pattern)
    else:
        typer.echo(f"Path does not exist: {path}", err=True)
        raise typer.Exit(code=1)


def ingest_directory(
    directory: Path,
    *,
    batch_size: int,
    max_workers: int,
    pattern: str = "*.jsonl",
) -> int:
    """Ingest all JSONL files in a directory using parallel workers."""
    files = sorted(directory.glob(pattern))
    if not files:
        logger.warning("No JSONL files found in %s", directory)
        return 0

    logger.info("Found %d JSONL files to ingest", len(files))

    file_paths = [str(file) for file in files]
    total_rows = 0

    kwargs_list = [{"file_path": fp, "batch_size": batch_size} for fp in file_paths]
    executor_results = parallelize_process(ingest_file, kwargs_list, max_workers=max_workers)
    total_rows = sum(executor_results.results)

    logger.info("Ingestion complete — %d total rows across %d files", total_rows, len(files))
    return total_rows


def ingest_file(file_path: str, *, batch_size: int) -> int:
    """Ingest a single JSONL file into the posts table. Returns total rows inserted."""
    path = Path(file_path)
    engine = get_postgres_engine(name="DATA_SCIENCE_DEV")
    total_rows = 0

    with Session(engine) as session:
        for batch in read_jsonl_batches(path, batch_size):
            inserted = _ingest_batch(session, batch)
            total_rows += inserted
            logger.info("  %s: inserted %d rows (total: %d)", path.name, inserted, total_rows)

    logger.info("Finished %s — %d rows", path.name, total_rows)
    return total_rows


def _ingest_batch(session: Session, batch: list[dict]) -> int:
    """Try bulk insert; on failure, binary-split to isolate bad rows."""
    if not batch:
        return 0

    try:
        statement = insert(Posts).values(batch).on_conflict_do_nothing(index_elements=["post_id"])
        result = session.execute(statement)
        session.commit()
    except (OSError, SQLAlchemyError) as error:
        session.rollback()

        if len(batch) == 1:
            logger.exception("Skipping bad row post_id=%s", batch[0].get("post_id"))
            session.add(
                FailedIngestion(
                    raw_line=json.dumps(batch[0], default=str),
                    error=str(error),
                )
            )
            session.commit()
            return 0

        midpoint = len(batch) // 2
        left = _ingest_batch(session, batch[:midpoint])
        right = _ingest_batch(session, batch[midpoint:])
        return left + right
    else:
        return result.rowcount


def read_jsonl_batches(file_path: Path, batch_size: int) -> Iterator[list[dict]]:
    """Stream a JSONL file and yield batches of transformed rows."""
    batch: list[dict] = []
    with file_path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            row = transform_row(json.loads(line))
            batch.append(row)
            if len(batch) >= batch_size:
                yield batch
                batch = []
    if batch:
        yield batch


def transform_row(raw: dict) -> dict:
    """Transform a raw JSONL row into a dict matching the Posts table columns."""
    raw["date"] = parse_date(raw["date"])
    if raw.get("langs") is not None:
        raw["langs"] = json.dumps(raw["langs"])
    return raw


def parse_date(raw_date: int) -> datetime:
    """Parse compact YYYYMMDDHHmm integer into a naive datetime (input is UTC by spec)."""
    return datetime(
        raw_date // 100000000,
        (raw_date // 1000000) % 100,
        (raw_date // 10000) % 100,
        (raw_date // 100) % 100,
        raw_date % 100,
        tzinfo=UTC,
    )


if __name__ == "__main__":
    app()

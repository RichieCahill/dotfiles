"""Ingestion pipeline for loading JSONL post files into the weekly-partitioned posts table.

Usage:
    ingest-posts /path/to/files/
    ingest-posts /path/to/single_file.jsonl
    ingest-posts /data/dir/ --workers 4 --batch-size 5000
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path  # noqa: TC003 this is needed for typer
from typing import TYPE_CHECKING, Annotated

import orjson
import psycopg
import typer

from python.common import configure_logger
from python.orm.common import get_connection_info
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
    configure_logger(level="INFO")

    logger.info("starting ingest-posts")
    logger.info("path=%s batch_size=%d workers=%d pattern=%s", path, batch_size, workers, pattern)
    if path.is_file():
        ingest_file(path, batch_size=batch_size)
    elif path.is_dir():
        ingest_directory(path, batch_size=batch_size, max_workers=workers, pattern=pattern)
    else:
        typer.echo(f"Path does not exist: {path}", err=True)
        raise typer.Exit(code=1)

    logger.info("ingest-posts done")


def ingest_directory(
    directory: Path,
    *,
    batch_size: int,
    max_workers: int,
    pattern: str = "*.jsonl",
) -> None:
    """Ingest all JSONL files in a directory using parallel workers."""
    files = sorted(directory.glob(pattern))
    if not files:
        logger.warning("No JSONL files found in %s", directory)
        return

    logger.info("Found %d JSONL files to ingest", len(files))

    kwargs_list = [{"path": fp, "batch_size": batch_size} for fp in files]
    parallelize_process(ingest_file, kwargs_list, max_workers=max_workers)


SCHEMA = "main"

COLUMNS = (
    "post_id",
    "user_id",
    "instance",
    "date",
    "text",
    "langs",
    "like_count",
    "reply_count",
    "repost_count",
    "reply_to",
    "replied_author",
    "thread_root",
    "thread_root_author",
    "repost_from",
    "reposted_author",
    "quotes",
    "quoted_author",
    "labels",
    "sent_label",
    "sent_score",
)

INSERT_FROM_STAGING = f"""
    INSERT INTO {SCHEMA}.posts ({", ".join(COLUMNS)})
    SELECT {", ".join(COLUMNS)} FROM pg_temp.staging
    ON CONFLICT (post_id, date) DO NOTHING
"""  # noqa: S608

FAILED_INSERT = f"""
    INSERT INTO {SCHEMA}.failed_ingestion (raw_line, error)
    VALUES (%(raw_line)s, %(error)s)
"""  # noqa: S608


def get_psycopg_connection() -> psycopg.Connection:
    """Create a raw psycopg3 connection from environment variables."""
    database, host, port, username, password = get_connection_info("DATA_SCIENCE_DEV")
    return psycopg.connect(
        dbname=database,
        host=host,
        port=int(port),
        user=username,
        password=password,
        autocommit=False,
    )


def ingest_file(path: Path, *, batch_size: int) -> None:
    """Ingest a single JSONL file into the posts table."""
    log_trigger = max(100_000 // batch_size, 1)
    failed_lines: list[dict] = []
    try:
        with get_psycopg_connection() as connection:
            for index, batch in enumerate(read_jsonl_batches(path, batch_size, failed_lines), 1):
                ingest_batch(connection, batch)
                if index % log_trigger == 0:
                    logger.info("Ingested %d batches (%d rows) from %s", index, index * batch_size, path)

            if failed_lines:
                logger.warning("Recording %d malformed lines from %s", len(failed_lines), path.name)
                with connection.cursor() as cursor:
                    cursor.executemany(FAILED_INSERT, failed_lines)
                connection.commit()
    except Exception:
        logger.exception("Failed to ingest file: %s", path)
        raise


def ingest_batch(connection: psycopg.Connection, batch: list[dict]) -> None:
    """COPY batch into a temp staging table, then INSERT ... ON CONFLICT into posts."""
    if not batch:
        return

    try:
        with connection.cursor() as cursor:
            cursor.execute(f"""
                CREATE TEMP TABLE IF NOT EXISTS staging
                (LIKE {SCHEMA}.posts INCLUDING DEFAULTS)
                ON COMMIT DELETE ROWS
            """)
            cursor.execute("TRUNCATE pg_temp.staging")

            with cursor.copy(f"COPY pg_temp.staging ({', '.join(COLUMNS)}) FROM STDIN") as copy:
                for row in batch:
                    copy.write_row(tuple(row.get(column) for column in COLUMNS))

            cursor.execute(INSERT_FROM_STAGING)
        connection.commit()
    except Exception as error:
        connection.rollback()

        if len(batch) == 1:
            logger.exception("Skipping bad row post_id=%s", batch[0].get("post_id"))
            with connection.cursor() as cursor:
                cursor.execute(
                    FAILED_INSERT,
                    {
                        "raw_line": orjson.dumps(batch[0], default=str).decode(),
                        "error": str(error),
                    },
                )
            connection.commit()
            return

        midpoint = len(batch) // 2
        ingest_batch(connection, batch[:midpoint])
        ingest_batch(connection, batch[midpoint:])


def read_jsonl_batches(file_path: Path, batch_size: int, failed_lines: list[dict]) -> Iterator[list[dict]]:
    """Stream a JSONL file and yield batches of transformed rows."""
    batch: list[dict] = []
    with file_path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            batch.extend(parse_line(line, file_path, failed_lines))
            if len(batch) >= batch_size:
                yield batch
                batch = []
    if batch:
        yield batch


def parse_line(line: str, file_path: Path, failed_lines: list[dict]) -> Iterator[dict]:
    """Parse a JSONL line, handling concatenated JSON objects."""
    try:
        yield transform_row(orjson.loads(line))
    except orjson.JSONDecodeError:
        if "}{" not in line:
            logger.warning("Skipping malformed line in %s: %s", file_path.name, line[:120])
            failed_lines.append({"raw_line": line, "error": "malformed JSON"})
            return
        fragments = line.replace("}{", "}\n{").split("\n")
        for fragment in fragments:
            try:
                yield transform_row(orjson.loads(fragment))
            except (orjson.JSONDecodeError, KeyError, ValueError) as error:
                logger.warning("Skipping malformed fragment in %s: %s", file_path.name, fragment[:120])
                failed_lines.append({"raw_line": fragment, "error": str(error)})
    except Exception as error:
        logger.exception("Skipping bad row in %s: %s", file_path.name, line[:120])
        failed_lines.append({"raw_line": line, "error": str(error)})


def transform_row(raw: dict) -> dict:
    """Transform a raw JSONL row into a dict matching the Posts table columns."""
    raw["date"] = parse_date(raw["date"])
    if raw.get("langs") is not None:
        raw["langs"] = orjson.dumps(raw["langs"])
    if raw.get("text") is not None:
        raw["text"] = raw["text"].replace("\x00", "")
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

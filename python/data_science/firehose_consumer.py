"""Kafka consumer that ingests Bluesky posts into the partitioned Posts table.

Consumes Jetstream messages from Kafka, transforms them into Posts rows,
and batch-inserts them into PostgreSQL with manual offset commits.

Usage:
    firehose-consumer
    firehose-consumer --kafka-servers kafka:9092 --batch-size 500
"""

from __future__ import annotations

import json
import logging
import signal
from os import getenv
from threading import Event
from typing import Annotated

import typer
from confluent_kafka import Consumer, KafkaError, KafkaException
from sqlalchemy.orm import Session

from python.data_science.bluesky_transform import is_post_create, transform_jetstream_post
from python.data_science.ingest_posts import ingest_batch
from python.orm.common import get_postgres_engine
from python.orm.data_science_dev.posts.failed_ingestion import FailedIngestion

logger = logging.getLogger(__name__)

DEFAULT_TOPIC = "bluesky.firehose.posts"
DEFAULT_KAFKA_SERVERS = "localhost:9092"
DEFAULT_GROUP_ID = "bluesky-posts-ingestor"
DEFAULT_BATCH_SIZE = 500
POLL_TIMEOUT_SECONDS = 5.0

shutdown_event = Event()

app = typer.Typer(help="Consume Bluesky posts from Kafka and ingest into PostgreSQL.")


@app.command()
def main(
    kafka_servers: Annotated[str, typer.Option(help="Kafka bootstrap servers")] = "",
    topic: Annotated[str, typer.Option(help="Kafka topic to consume from")] = "",
    group_id: Annotated[str, typer.Option(help="Kafka consumer group ID")] = "",
    batch_size: Annotated[int, typer.Option(help="Messages per DB insert batch")] = DEFAULT_BATCH_SIZE,
) -> None:
    """Consume Bluesky posts from Kafka and ingest into the partitioned posts table."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )

    servers = kafka_servers or getenv("KAFKA_BOOTSTRAP_SERVERS", DEFAULT_KAFKA_SERVERS)
    topic_name = topic or getenv("BLUESKY_FIREHOSE_TOPIC", DEFAULT_TOPIC)
    group = group_id or getenv("KAFKA_GROUP_ID", DEFAULT_GROUP_ID)

    signal.signal(signal.SIGTERM, _handle_shutdown)
    signal.signal(signal.SIGINT, _handle_shutdown)

    consumer = _create_consumer(servers, group)
    consumer.subscribe([topic_name])

    engine = get_postgres_engine(name="DATA_SCIENCE_DEV")
    total_inserted = 0

    logger.info("Starting firehose consumer: topic=%s group=%s batch_size=%d", topic_name, group, batch_size)

    try:
        with Session(engine) as session:
            while not shutdown_event.is_set():
                inserted = _consume_batch(consumer, session, batch_size)
                total_inserted += inserted
                if inserted > 0:
                    logger.info("Batch inserted %d rows (total: %d)", inserted, total_inserted)
    except KafkaException:
        logger.exception("Fatal Kafka error")
    finally:
        logger.info("Closing consumer (total inserted: %d)", total_inserted)
        consumer.close()


def _consume_batch(consumer: Consumer, session: Session, batch_size: int) -> int:
    """Poll a batch of messages, transform, and insert into the database.

    Args:
        consumer: The Kafka consumer instance.
        session: SQLAlchemy database session.
        batch_size: Maximum number of messages to consume per batch.

    Returns:
        Number of rows successfully inserted.
    """
    messages = consumer.consume(num_messages=batch_size, timeout=POLL_TIMEOUT_SECONDS)
    if not messages:
        return 0

    rows: list[dict] = []
    for message in messages:
        error = message.error()
        if error is not None:
            if error.code() == KafkaError._PARTITION_EOF:  # noqa: SLF001 — confluent-kafka exposes this as a pseudo-private constant; no public alternative exists
                continue
            logger.error("Consumer error: %s", error)
            continue

        row = _safe_transform(message.value(), session)
        if row is not None:
            rows.append(row)

    if not rows:
        consumer.commit(asynchronous=False)
        return 0

    inserted = ingest_batch(session, rows)
    consumer.commit(asynchronous=False)
    return inserted


def _safe_transform(raw_value: bytes | None, session: Session) -> dict | None:
    """Transform a Kafka message value into a Posts row, logging failures.

    Args:
        raw_value: Raw message bytes from Kafka.
        session: SQLAlchemy session for logging failures.

    Returns:
        A transformed row dict, or None if transformation failed.
    """
    if raw_value is None:
        return None

    try:
        message = json.loads(raw_value)
    except (json.JSONDecodeError, UnicodeDecodeError):
        logger.exception("Failed to decode Kafka message")
        _log_failed_ingestion(session, raw_value, "JSON decode error")
        return None

    if not is_post_create(message):
        return None

    try:
        return transform_jetstream_post(message)
    except (KeyError, ValueError, TypeError):
        logger.exception("Failed to transform Jetstream message")
        _log_failed_ingestion(session, raw_value, "Transform error")
        return None


def _log_failed_ingestion(session: Session, raw_value: bytes, error: str) -> None:
    """Log a failed ingestion to the FailedIngestion table.

    Args:
        session: SQLAlchemy session.
        raw_value: The raw message bytes.
        error: Description of the error.
    """
    try:
        session.add(
            FailedIngestion(
                raw_line=raw_value.decode(errors="replace")[:10000],
                error=error,
            )
        )
        session.commit()
    except Exception:
        session.rollback()
        logger.exception("Failed to log ingestion failure")


def _create_consumer(servers: str, group: str) -> Consumer:
    """Create a configured Kafka consumer.

    Args:
        servers: Kafka bootstrap servers string.
        group: Consumer group ID.

    Returns:
        A configured confluent_kafka.Consumer.
    """
    config = {
        "bootstrap.servers": servers,
        "group.id": group,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,
        "max.poll.interval.ms": 300000,
        "fetch.min.bytes": 1024,
        "session.timeout.ms": 30000,
    }
    return Consumer(config)


def _handle_shutdown(_signum: int, _frame: object) -> None:
    """Signal handler to trigger graceful shutdown."""
    logger.info("Shutdown signal received")
    shutdown_event.set()


if __name__ == "__main__":
    app()

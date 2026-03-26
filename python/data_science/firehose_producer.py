"""Bluesky Jetstream firehose to Kafka producer.

Connects to the Bluesky Jetstream WebSocket API with zstd compression,
filters for post creation events, and produces them to a Kafka topic.

Usage:
    firehose-producer
    firehose-producer --kafka-servers kafka:9092 --topic bluesky.firehose.posts
"""

from __future__ import annotations

import json
import logging
import signal
from os import getenv
from threading import Event
from typing import Annotated

import typer
from compression import zstd
from confluent_kafka import KafkaError, KafkaException, Producer
from websockets.exceptions import ConnectionClosed
from websockets.sync.client import connect

logger = logging.getLogger(__name__)

JETSTREAM_URL = "wss://jetstream2.us-east.bsky.network/subscribe"
DEFAULT_TOPIC = "bluesky.firehose.posts"
DEFAULT_KAFKA_SERVERS = "localhost:9092"
POLL_INTERVAL = 100
POST_COLLECTION = "app.bsky.feed.post"

shutdown_event = Event()

app = typer.Typer(help="Stream Bluesky firehose posts into Kafka.")


@app.command()
def main(
    kafka_servers: Annotated[str, typer.Option(help="Kafka bootstrap servers")] = "",
    topic: Annotated[str, typer.Option(help="Kafka topic to produce to")] = "",
    collections: Annotated[str, typer.Option(help="Comma-separated collections to subscribe to")] = POST_COLLECTION,
) -> None:
    """Connect to Bluesky Jetstream and produce post events to Kafka."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )

    servers = kafka_servers or getenv("KAFKA_BOOTSTRAP_SERVERS", DEFAULT_KAFKA_SERVERS)
    topic_name = topic or getenv("BLUESKY_FIREHOSE_TOPIC", DEFAULT_TOPIC)

    signal.signal(signal.SIGTERM, _handle_shutdown)
    signal.signal(signal.SIGINT, _handle_shutdown)

    producer = _create_producer(servers)
    cursor: int | None = None

    logger.info("Starting firehose producer → %s on %s", topic_name, servers)

    while not shutdown_event.is_set():
        try:
            cursor = _stream_loop(producer, topic_name, collections, cursor)
        except (ConnectionClosed, OSError):
            logger.exception("WebSocket disconnected, reconnecting")
        except KafkaException:
            logger.exception("Kafka error, reconnecting")

        if not shutdown_event.is_set():
            logger.info("Reconnecting in 5 seconds (cursor=%s)", cursor)
            shutdown_event.wait(timeout=5)

    logger.info("Shutting down, flushing producer")
    producer.flush(timeout=30)
    logger.info("Producer shutdown complete")


def _stream_loop(
    producer: Producer,
    topic: str,
    collections: str,
    cursor: int | None,
) -> int | None:
    """Connect to Jetstream and stream messages to Kafka until disconnected.

    Args:
        producer: The Kafka producer instance.
        topic: Kafka topic name.
        collections: Comma-separated AT Protocol collections to subscribe to.
        cursor: Optional microsecond timestamp to resume from.

    Returns:
        The last processed time_us cursor value.
    """
    url = _build_jetstream_url(collections, cursor)
    logger.info("Connecting to %s", url)

    message_count = 0
    last_cursor = cursor

    with connect(url, additional_headers={"Accept-Encoding": "zstd"}) as websocket:
        logger.info("Connected to Jetstream")

        while not shutdown_event.is_set():
            try:
                raw_frame = websocket.recv(timeout=10)
            except TimeoutError:
                producer.poll(0)
                continue

            text = _decode_frame(raw_frame)
            message = json.loads(text)

            time_us = message.get("time_us")
            if time_us is not None:
                last_cursor = time_us

            if not _is_post_create(message):
                continue

            did = message.get("did", "")

            try:
                producer.produce(
                    topic,
                    key=did.encode(),
                    value=text.encode() if isinstance(text, str) else text,
                    callback=_delivery_callback,
                )
            except BufferError:
                logger.warning("Producer buffer full, flushing")
                producer.flush(timeout=10)
                producer.produce(
                    topic,
                    key=did.encode(),
                    value=text.encode() if isinstance(text, str) else text,
                    callback=_delivery_callback,
                )

            message_count += 1
            if message_count % POLL_INTERVAL == 0:
                producer.poll(0)

            if message_count % 10000 == 0:
                logger.info("Produced %d messages (cursor=%s)", message_count, last_cursor)

    return last_cursor


def _build_jetstream_url(collections: str, cursor: int | None) -> str:
    """Build the Jetstream WebSocket URL with query parameters.

    Args:
        collections: Comma-separated collection names.
        cursor: Optional microsecond timestamp for resumption.

    Returns:
        The full WebSocket URL.
    """
    params = ["compress=true"]
    for raw_collection in collections.split(","):
        cleaned = raw_collection.strip()
        if cleaned:
            params.append(f"wantedCollections={cleaned}")
    if cursor is not None:
        params.append(f"cursor={cursor}")
    return f"{JETSTREAM_URL}?{'&'.join(params)}"


def _decode_frame(frame: str | bytes) -> str:
    """Decode a WebSocket frame, decompressing zstd if binary.

    Jetstream with compress=true sends zstd-compressed binary frames.

    Args:
        frame: Raw WebSocket frame data.

    Returns:
        The decoded JSON string.
    """
    if isinstance(frame, bytes):
        return zstd.decompress(frame).decode()
    return frame


def _is_post_create(message: dict) -> bool:
    """Check if a Jetstream message is a post creation commit."""
    if message.get("kind") != "commit":
        return False
    commit = message.get("commit", {})
    return commit.get("operation") == "create" and commit.get("collection") == POST_COLLECTION


def _create_producer(servers: str) -> Producer:
    """Create a configured Kafka producer.

    Args:
        servers: Kafka bootstrap servers string.

    Returns:
        A configured confluent_kafka.Producer.
    """
    config = {
        "bootstrap.servers": servers,
        "linger.ms": 50,
        "batch.size": 65536,
        "compression.type": "zstd",
        "acks": "all",
        "retries": 5,
        "retry.backoff.ms": 500,
    }
    return Producer(config)


def _delivery_callback(error: KafkaError | None, _message: object) -> None:
    """Log delivery failures from the Kafka producer."""
    if error is not None:
        logger.error("Kafka delivery failed: %s", error)


def _handle_shutdown(_signum: int, _frame: object) -> None:
    """Signal handler to trigger graceful shutdown."""
    logger.info("Shutdown signal received")
    shutdown_event.set()


if __name__ == "__main__":
    app()

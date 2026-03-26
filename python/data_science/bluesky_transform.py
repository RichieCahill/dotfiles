"""Transform Bluesky Jetstream messages into rows matching the Posts table schema."""

from __future__ import annotations

import json
import logging
from datetime import datetime

from python.data_science.bluesky_ids import (
    did_to_user_id,
    post_id_from_uri,
    tid_to_integer,
    user_id_from_uri,
)

logger = logging.getLogger(__name__)

INSTANCE = "bsky"
POST_COLLECTION = "app.bsky.feed.post"
EMBED_RECORD_TYPE = "app.bsky.embed.record"
EMBED_RECORD_WITH_MEDIA_TYPE = "app.bsky.embed.recordWithMedia"


def transform_jetstream_post(message: dict) -> dict:
    """Transform a Jetstream commit message into a dict matching Posts table columns.

    Expects a Jetstream message with kind=commit, operation=create,
    collection=app.bsky.feed.post.

    Args:
        message: The full Jetstream JSON message.

    Returns:
        A dict with keys matching the Posts table columns.
    """
    did = message["did"]
    commit = message["commit"]
    record = commit["record"]

    row: dict = {
        "post_id": tid_to_integer(commit["rkey"]),
        "user_id": did_to_user_id(did),
        "instance": INSTANCE,
        "date": datetime.fromisoformat(record["createdAt"]),
        "text": record.get("text", ""),
        "langs": _extract_langs(record),
        "like_count": 0,
        "reply_count": 0,
        "repost_count": 0,
        "reply_to": None,
        "replied_author": None,
        "thread_root": None,
        "thread_root_author": None,
        "repost_from": None,
        "reposted_author": None,
        "quotes": None,
        "quoted_author": None,
        "labels": _extract_labels(record),
        "sent_label": None,
        "sent_score": None,
    }

    _extract_reply_refs(record, row)
    _extract_quote_refs(record, row)

    return row


def is_post_create(message: dict) -> bool:
    """Check if a Jetstream message is a post creation event.

    Args:
        message: The full Jetstream JSON message.

    Returns:
        True if this is a create commit for app.bsky.feed.post.
    """
    if message.get("kind") != "commit":
        return False
    commit = message.get("commit", {})
    return commit.get("operation") == "create" and commit.get("collection") == POST_COLLECTION


def _extract_langs(record: dict) -> str | None:
    """Extract langs array as a JSON string, or None if absent."""
    langs = record.get("langs")
    if langs is None:
        return None
    return json.dumps(langs)


def _extract_labels(record: dict) -> str | None:
    """Extract self-labels as a JSON string, or None if absent."""
    labels_obj = record.get("labels")
    if labels_obj is None:
        return None
    values = labels_obj.get("values", [])
    if not values:
        return None
    label_strings = [label.get("val", "") for label in values]
    return json.dumps(label_strings)


def _extract_reply_refs(record: dict, row: dict) -> None:
    """Populate reply_to, replied_author, thread_root, thread_root_author from record.reply."""
    reply = record.get("reply")
    if reply is None:
        return

    parent = reply.get("parent", {})
    parent_uri = parent.get("uri")
    if parent_uri:
        row["reply_to"] = post_id_from_uri(parent_uri)
        row["replied_author"] = user_id_from_uri(parent_uri)

    root = reply.get("root", {})
    root_uri = root.get("uri")
    if root_uri:
        row["thread_root"] = post_id_from_uri(root_uri)
        row["thread_root_author"] = user_id_from_uri(root_uri)


def _extract_quote_refs(record: dict, row: dict) -> None:
    """Populate quotes and quoted_author from embed record references."""
    embed = record.get("embed")
    if embed is None:
        return

    embed_type = embed.get("$type", "")

    if embed_type == EMBED_RECORD_TYPE:
        _set_quote_from_record(embed.get("record", {}), row)
    elif embed_type == EMBED_RECORD_WITH_MEDIA_TYPE:
        inner_record = embed.get("record", {}).get("record", {})
        _set_quote_from_record(inner_record, row)


def _set_quote_from_record(record_ref: dict, row: dict) -> None:
    """Set quotes and quoted_author from a record reference object."""
    uri = record_ref.get("uri")
    if uri and POST_COLLECTION in uri:
        row["quotes"] = post_id_from_uri(uri)
        row["quoted_author"] = user_id_from_uri(uri)

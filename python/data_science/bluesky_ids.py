"""Utilities for converting Bluesky identifiers to numeric database IDs.

Handles DID-to-user_id hashing, TID-to-post_id decoding, and AT-URI parsing.
"""

from __future__ import annotations

import hashlib

TID_CHARSET = "234567abcdefghijklmnopqrstuvwxyz"
_TID_LENGTH = 13
_BIGINT_MASK = 0x7FFFFFFFFFFFFFFF
_AT_URI_SEGMENT_COUNT = 3


def did_to_user_id(did: str) -> int:
    """Convert a DID string to a deterministic 63-bit integer for user_id.

    Uses SHA-256, truncated to 63 bits (positive signed BigInteger range).
    Collision probability is negligible at Bluesky's scale (~tens of millions of users).

    Args:
        did: A Bluesky DID string, e.g. "did:plc:abc123".

    Returns:
        A positive 63-bit integer suitable for BigInteger storage.
    """
    digest = hashlib.sha256(did.encode()).digest()
    return int.from_bytes(digest[:8], "big") & _BIGINT_MASK


def tid_to_integer(tid: str) -> int:
    """Decode a Bluesky TID (base32-sortbase) into a 64-bit integer for post_id.

    TIDs are 13-character, base32-sortbase encoded identifiers that encode a
    microsecond timestamp plus a clock ID. They are globally unique by construction.

    Args:
        tid: A 13-character TID string, e.g. "3abc2defghijk".

    Returns:
        A positive integer suitable for BigInteger storage.

    Raises:
        ValueError: If the TID is malformed (wrong length or invalid characters).
    """
    if len(tid) != _TID_LENGTH:
        message = f"TID must be {_TID_LENGTH} characters, got {len(tid)}: {tid!r}"
        raise ValueError(message)

    result = 0
    for char in tid:
        index = TID_CHARSET.find(char)
        if index == -1:
            message = f"Invalid character {char!r} in TID {tid!r}"
            raise ValueError(message)
        result = result * 32 + index
    return result


def parse_at_uri(uri: str) -> tuple[str, str, str]:
    """Parse an AT-URI into its components.

    Args:
        uri: An AT-URI string, e.g. "at://did:plc:abc123/app.bsky.feed.post/3abc2defghijk".

    Returns:
        A tuple of (did, collection, rkey).

    Raises:
        ValueError: If the URI doesn't have the expected format.
    """
    stripped = uri.removeprefix("at://")
    parts = stripped.split("/", maxsplit=2)
    if len(parts) != _AT_URI_SEGMENT_COUNT:
        message = f"Expected {_AT_URI_SEGMENT_COUNT} path segments in AT-URI, got {len(parts)}: {uri!r}"
        raise ValueError(message)
    return parts[0], parts[1], parts[2]


def post_id_from_uri(uri: str) -> int:
    """Extract and decode the post_id (TID) from an AT-URI.

    Args:
        uri: An AT-URI pointing to a post.

    Returns:
        The post_id as an integer.
    """
    _did, _collection, rkey = parse_at_uri(uri)
    return tid_to_integer(rkey)


def user_id_from_uri(uri: str) -> int:
    """Extract and hash the user_id (DID) from an AT-URI.

    Args:
        uri: An AT-URI pointing to a post.

    Returns:
        The user_id as an integer.
    """
    did, _collection, _rkey = parse_at_uri(uri)
    return did_to_user_id(did)

"""Data science dev database ORM models."""

from __future__ import annotations

from python.orm.data_science_dev.posts import partitions  # noqa: F401 — registers partition classes in metadata
from python.orm.data_science_dev.posts.tables import Posts

__all__ = [
    "Posts",
]

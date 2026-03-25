"""Posts module — weekly-partitioned posts table and partition ORM models."""

from __future__ import annotations

from python.orm.data_science_dev.posts.failed_ingestion import FailedIngestion
from python.orm.data_science_dev.posts.tables import Posts

__all__ = [
    "FailedIngestion",
    "Posts",
]

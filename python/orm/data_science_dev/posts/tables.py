"""Posts parent table with PostgreSQL weekly range partitioning on date column."""

from __future__ import annotations

from python.orm.data_science_dev.base import DataScienceDevBase
from python.orm.data_science_dev.posts.columns import PostsColumns


class Posts(PostsColumns, DataScienceDevBase):
    """Parent partitioned table for posts, partitioned by week on `date`."""

    __tablename__ = "posts"
    __table_args__ = ({"postgresql_partition_by": "RANGE (date)"},)

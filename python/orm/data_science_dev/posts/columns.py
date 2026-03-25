"""Shared column definitions for the posts partitioned table family."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, SmallInteger, Text
from sqlalchemy.orm import Mapped, mapped_column


class PostsColumns:
    """Mixin providing all posts columns. Used by both the parent table and partitions."""

    post_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger)
    instance: Mapped[str]
    date: Mapped[datetime] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column(Text)
    langs: Mapped[str | None]
    like_count: Mapped[int]
    reply_count: Mapped[int]
    repost_count: Mapped[int]
    reply_to: Mapped[int | None] = mapped_column(BigInteger)
    replied_author: Mapped[int | None] = mapped_column(BigInteger)
    thread_root: Mapped[int | None] = mapped_column(BigInteger)
    thread_root_author: Mapped[int | None] = mapped_column(BigInteger)
    repost_from: Mapped[int | None] = mapped_column(BigInteger)
    reposted_author: Mapped[int | None] = mapped_column(BigInteger)
    quotes: Mapped[int | None] = mapped_column(BigInteger)
    quoted_author: Mapped[int | None] = mapped_column(BigInteger)
    labels: Mapped[str | None]
    sent_label: Mapped[int | None] = mapped_column(SmallInteger)
    sent_score: Mapped[float | None]

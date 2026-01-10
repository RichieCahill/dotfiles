"""Temporary ORM model."""

from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from python.orm.base import TableBase


class Temp(TableBase):
    """Temporary table for initial testing."""

    __tablename__ = "temp"

    name: Mapped[str] = mapped_column(String(255), nullable=False)

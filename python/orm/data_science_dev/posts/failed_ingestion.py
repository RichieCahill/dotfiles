"""Table for storing JSONL lines that failed during post ingestion."""

from __future__ import annotations

from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column

from python.orm.data_science_dev.base import DataScienceDevTableBase


class FailedIngestion(DataScienceDevTableBase):
    """Stores raw JSONL lines and their error messages when ingestion fails."""

    __tablename__ = "failed_ingestion"

    raw_line: Mapped[str] = mapped_column(Text)
    error: Mapped[str] = mapped_column(Text)

"""Bill model - legislation introduced in Congress."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from python.orm.data_science_dev.base import DataScienceDevTableBase

if TYPE_CHECKING:
    from python.orm.data_science_dev.congress.vote import Vote


class Bill(DataScienceDevTableBase):
    """Legislation with congress number, type, titles, status, and sponsor."""

    __tablename__ = "bill"

    congress: Mapped[int]
    bill_type: Mapped[str]
    number: Mapped[int]

    title: Mapped[str | None]
    title_short: Mapped[str | None]
    official_title: Mapped[str | None]

    status: Mapped[str | None]
    status_at: Mapped[date | None]

    sponsor_bioguide_id: Mapped[str | None]

    subjects_top_term: Mapped[str | None]

    votes: Mapped[list[Vote]] = relationship(
        "Vote",
        back_populates="bill",
    )
    bill_texts: Mapped[list[BillText]] = relationship(
        "BillText",
        back_populates="bill",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("congress", "bill_type", "number", name="uq_bill_congress_type_number"),
        Index("ix_bill_congress", "congress"),
    )


class BillText(DataScienceDevTableBase):
    """Stores different text versions of a bill (introduced, enrolled, etc.)."""

    __tablename__ = "bill_text"

    bill_id: Mapped[int] = mapped_column(ForeignKey("main.bill.id", ondelete="CASCADE"))
    version_code: Mapped[str]
    version_name: Mapped[str | None]
    text_content: Mapped[str | None]
    date: Mapped[date | None]

    bill: Mapped[Bill] = relationship("Bill", back_populates="bill_texts")

    __table_args__ = (UniqueConstraint("bill_id", "version_code", name="uq_bill_text_bill_id_version_code"),)

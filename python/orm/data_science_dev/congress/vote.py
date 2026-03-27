"""Vote model - roll call votes in Congress."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from python.orm.data_science_dev.base import DataScienceDevBase, DataScienceDevTableBase

if TYPE_CHECKING:
    from python.orm.data_science_dev.congress.bill import Bill
    from python.orm.data_science_dev.congress.legislator import Legislator
    from python.orm.data_science_dev.congress.vote import Vote


class VoteRecord(DataScienceDevBase):
    """Links a vote to a legislator with their position (Yea, Nay, etc.)."""

    __tablename__ = "vote_record"

    vote_id: Mapped[int] = mapped_column(
        ForeignKey("main.vote.id", ondelete="CASCADE"),
        primary_key=True,
    )
    legislator_id: Mapped[int] = mapped_column(
        ForeignKey("main.legislator.id", ondelete="CASCADE"),
        primary_key=True,
    )
    position: Mapped[str]

    vote: Mapped[Vote] = relationship("Vote", back_populates="vote_records")
    legislator: Mapped[Legislator] = relationship("Legislator", back_populates="vote_records")


class Vote(DataScienceDevTableBase):
    """Roll call votes with counts and optional bill linkage."""

    __tablename__ = "vote"

    congress: Mapped[int]
    chamber: Mapped[str]
    session: Mapped[int]
    number: Mapped[int]

    vote_type: Mapped[str | None]
    question: Mapped[str | None]
    result: Mapped[str | None]
    result_text: Mapped[str | None]

    vote_date: Mapped[date]

    yea_count: Mapped[int | None]
    nay_count: Mapped[int | None]
    not_voting_count: Mapped[int | None]
    present_count: Mapped[int | None]

    bill_id: Mapped[int | None] = mapped_column(ForeignKey("main.bill.id"))

    bill: Mapped[Bill | None] = relationship("Bill", back_populates="votes")
    vote_records: Mapped[list[VoteRecord]] = relationship(
        "VoteRecord",
        back_populates="vote",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint(
            "congress",
            "chamber",
            "session",
            "number",
            name="uq_vote_congress_chamber_session_number",
        ),
        Index("ix_vote_date", "vote_date"),
        Index("ix_vote_congress_chamber", "congress", "chamber"),
    )

"""Congress Tracker database models."""

from __future__ import annotations

from datetime import date

from sqlalchemy import ForeignKey, Index, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from python.orm.richie.base import RichieBase, TableBase


class Legislator(TableBase):
    """Legislator model - members of Congress."""

    __tablename__ = "legislator"

    # Natural key - bioguide ID is the authoritative identifier
    bioguide_id: Mapped[str] = mapped_column(Text, unique=True, index=True)

    # Other IDs for cross-referencing
    thomas_id: Mapped[str | None]
    lis_id: Mapped[str | None]
    govtrack_id: Mapped[int | None]
    opensecrets_id: Mapped[str | None]
    fec_ids: Mapped[str | None]  # JSON array stored as string

    # Name info
    first_name: Mapped[str]
    last_name: Mapped[str]
    official_full_name: Mapped[str | None]
    nickname: Mapped[str | None]

    # Bio
    birthday: Mapped[date | None]
    gender: Mapped[str | None]  # M/F

    # Current term info (denormalized for query efficiency)
    current_party: Mapped[str | None]
    current_state: Mapped[str | None]
    current_district: Mapped[int | None]  # House only
    current_chamber: Mapped[str | None]  # rep/sen

    # Relationships
    vote_records: Mapped[list[VoteRecord]] = relationship(
        "VoteRecord",
        back_populates="legislator",
        cascade="all, delete-orphan",
    )


class Bill(TableBase):
    """Bill model - legislation introduced in Congress."""

    __tablename__ = "bill"

    # Composite natural key: congress + bill_type + number
    congress: Mapped[int]
    bill_type: Mapped[str]  # hr, s, hres, sres, hjres, sjres
    number: Mapped[int]

    # Bill info
    title: Mapped[str | None]
    title_short: Mapped[str | None]
    official_title: Mapped[str | None]

    # Status
    status: Mapped[str | None]
    status_at: Mapped[date | None]

    # Sponsor
    sponsor_bioguide_id: Mapped[str | None]

    # Subjects
    subjects_top_term: Mapped[str | None]

    # Relationships
    votes: Mapped[list[Vote]] = relationship(
        "Vote",
        back_populates="bill",
    )

    __table_args__ = (
        UniqueConstraint("congress", "bill_type", "number", name="uq_bill_congress_type_number"),
        Index("ix_bill_congress", "congress"),
    )


class Vote(TableBase):
    """Vote model - roll call votes in Congress."""

    __tablename__ = "vote"

    # Composite natural key: congress + chamber + session + number
    congress: Mapped[int]
    chamber: Mapped[str]  # house/senate
    session: Mapped[int]
    number: Mapped[int]

    # Vote details
    vote_type: Mapped[str | None]
    question: Mapped[str | None]
    result: Mapped[str | None]
    result_text: Mapped[str | None]

    # Timing
    vote_date: Mapped[date]

    # Vote counts (denormalized for efficiency)
    yea_count: Mapped[int | None]
    nay_count: Mapped[int | None]
    not_voting_count: Mapped[int | None]
    present_count: Mapped[int | None]

    # Related bill (optional - not all votes are on bills)
    bill_id: Mapped[int | None] = mapped_column(ForeignKey("main.bill.id"))

    # Relationships
    bill: Mapped[Bill | None] = relationship("Bill", back_populates="votes")
    vote_records: Mapped[list[VoteRecord]] = relationship(
        "VoteRecord",
        back_populates="vote",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("congress", "chamber", "session", "number", name="uq_vote_congress_chamber_session_number"),
        Index("ix_vote_date", "vote_date"),
        Index("ix_vote_congress_chamber", "congress", "chamber"),
    )


class VoteRecord(RichieBase):
    """Association table: Vote <-> Legislator with position."""

    __tablename__ = "vote_record"

    vote_id: Mapped[int] = mapped_column(
        ForeignKey("main.vote.id", ondelete="CASCADE"),
        primary_key=True,
    )
    legislator_id: Mapped[int] = mapped_column(
        ForeignKey("main.legislator.id", ondelete="CASCADE"),
        primary_key=True,
    )
    position: Mapped[str]  # Yea, Nay, Not Voting, Present

    # Relationships
    vote: Mapped[Vote] = relationship("Vote", back_populates="vote_records")
    legislator: Mapped[Legislator] = relationship("Legislator", back_populates="vote_records")

"""Legislator model - members of Congress."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from python.orm.data_science_dev.base import DataScienceDevTableBase

if TYPE_CHECKING:
    from python.orm.data_science_dev.congress.vote import VoteRecord


class Legislator(DataScienceDevTableBase):
    """Members of Congress with identification and current term info."""

    __tablename__ = "legislator"

    bioguide_id: Mapped[str] = mapped_column(Text, unique=True, index=True)

    thomas_id: Mapped[str | None]
    lis_id: Mapped[str | None]
    govtrack_id: Mapped[int | None]
    opensecrets_id: Mapped[str | None]
    fec_ids: Mapped[str | None]

    first_name: Mapped[str]
    last_name: Mapped[str]
    official_full_name: Mapped[str | None]
    nickname: Mapped[str | None]

    birthday: Mapped[date | None]
    gender: Mapped[str | None]

    current_party: Mapped[str | None]
    current_state: Mapped[str | None]
    current_district: Mapped[int | None]
    current_chamber: Mapped[str | None]

    vote_records: Mapped[list[VoteRecord]] = relationship(
        "VoteRecord",
        back_populates="legislator",
        cascade="all, delete-orphan",
    )

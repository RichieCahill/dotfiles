"""Signal bot device registry models."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column

from python.orm.richie.base import TableBase
from python.signal_bot.models import TrustLevel


class SignalDevice(TableBase):
    """A Signal device tracked by phone number and safety number."""

    __tablename__ = "signal_device"

    phone_number: Mapped[str] = mapped_column(String(50), unique=True)
    safety_number: Mapped[str | None]
    trust_level: Mapped[TrustLevel] = mapped_column(
        ENUM(TrustLevel, name="trust_level", create_type=True, schema="main"),
        default=TrustLevel.UNVERIFIED,
    )
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True))

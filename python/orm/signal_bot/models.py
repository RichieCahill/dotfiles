"""Signal bot device, role, and dead letter ORM models."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, SmallInteger, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from python.orm.signal_bot.base import SignalBotTableBase, SignalBotTableBaseSmall
from python.signal_bot.models import MessageStatus, TrustLevel


class RoleRecord(SignalBotTableBaseSmall):
    """Lookup table for RBAC roles, keyed by smallint."""

    __tablename__ = "role"

    name: Mapped[str] = mapped_column(String(50), unique=True)


class DeviceRole(SignalBotTableBase):
    """Association between a device and a role."""

    __tablename__ = "device_role"
    __table_args__ = (
        UniqueConstraint("device_id", "role_id", name="uq_device_role_device_role"),
        {"schema": "main"},
    )

    device_id: Mapped[int] = mapped_column(ForeignKey("main.signal_device.id"))
    role_id: Mapped[int] = mapped_column(SmallInteger, ForeignKey("main.role.id"))


class SignalDevice(SignalBotTableBase):
    """A Signal device tracked by phone number and safety number."""

    __tablename__ = "signal_device"

    phone_number: Mapped[str] = mapped_column(String(50), unique=True)
    safety_number: Mapped[str | None]
    trust_level: Mapped[TrustLevel] = mapped_column(
        ENUM(TrustLevel, name="trust_level", create_type=True, schema="main"),
        default=TrustLevel.UNVERIFIED,
    )
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    roles: Mapped[list[RoleRecord]] = relationship(secondary=DeviceRole.__table__)


class DeadLetterMessage(SignalBotTableBase):
    """A Signal message that failed processing and was sent to the dead letter queue."""

    __tablename__ = "dead_letter_message"

    source: Mapped[str]
    message: Mapped[str] = mapped_column(Text)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[MessageStatus] = mapped_column(
        ENUM(MessageStatus, name="message_status", create_type=True, schema="main"),
        default=MessageStatus.UNPROCESSED,
    )

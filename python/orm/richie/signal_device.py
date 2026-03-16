"""Signal bot device and role ORM models."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, SmallInteger, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from python.orm.richie.base import TableBase, TableBaseSmall
from python.signal_bot.models import TrustLevel


class RoleRecord(TableBaseSmall):
    """Lookup table for RBAC roles, keyed by smallint."""

    __tablename__ = "role"

    name: Mapped[str] = mapped_column(String(50), unique=True)


class DeviceRole(TableBase):
    """Association between a device and a role."""

    __tablename__ = "device_role"
    __table_args__ = (
        UniqueConstraint("device_id", "role_id", name="uq_device_role_device_role"),
        {"schema": "main"},
    )

    device_id: Mapped[int] = mapped_column(ForeignKey("main.signal_device.id"))
    role_id: Mapped[int] = mapped_column(SmallInteger, ForeignKey("main.role.id"))


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

    roles: Mapped[list[RoleRecord]] = relationship(secondary=DeviceRole.__table__)

"""Signal bot database ORM base."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, MetaData, SmallInteger, func
from sqlalchemy.ext.declarative import AbstractConcreteBase
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from python.orm.common import NAMING_CONVENTION


class SignalBotBase(DeclarativeBase):
    """Base class for signal_bot database ORM models."""

    schema_name = "main"

    metadata = MetaData(
        schema=schema_name,
        naming_convention=NAMING_CONVENTION,
    )


class _TableMixin:
    """Shared timestamp columns for all table bases."""

    created: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class SignalBotTableBaseSmall(_TableMixin, AbstractConcreteBase, SignalBotBase):
    """Table with SmallInteger primary key."""

    __abstract__ = True

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)


class SignalBotTableBase(_TableMixin, AbstractConcreteBase, SignalBotBase):
    """Table with Integer primary key."""

    __abstract__ = True

    id: Mapped[int] = mapped_column(primary_key=True)

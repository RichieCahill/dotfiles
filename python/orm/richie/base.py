"""Richie database ORM base."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, MetaData, func
from sqlalchemy.ext.declarative import AbstractConcreteBase
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from python.orm.common import NAMING_CONVENTION


class RichieBase(DeclarativeBase):
    """Base class for richie database ORM models."""

    schema_name = "main"

    metadata = MetaData(
        schema=schema_name,
        naming_convention=NAMING_CONVENTION,
    )


class TableBase(AbstractConcreteBase, RichieBase):
    """Abstract concrete base for richie tables with IDs and timestamps."""

    __abstract__ = True

    id: Mapped[int] = mapped_column(primary_key=True)
    created: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

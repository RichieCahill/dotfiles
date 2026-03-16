"""Richie database ORM base."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, MetaData, SmallInteger, func
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


class TableBaseSmall(_TableMixin, AbstractConcreteBase, RichieBase):
    """Table with SmallInteger primary key."""

    __abstract__ = True

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)


class TableBase(_TableMixin, AbstractConcreteBase, RichieBase):
    """Table with Integer primary key."""

    __abstract__ = True

    id: Mapped[int] = mapped_column(primary_key=True)


class TableBaseBig(_TableMixin, AbstractConcreteBase, RichieBase):
    """Table with BigInteger primary key."""

    __abstract__ = True

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

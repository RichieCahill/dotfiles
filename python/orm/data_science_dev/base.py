"""Data science dev database ORM base."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, MetaData, func
from sqlalchemy.ext.declarative import AbstractConcreteBase
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from python.orm.common import NAMING_CONVENTION


class DataScienceDevBase(DeclarativeBase):
    """Base class for data_science_dev database ORM models."""

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


class DataScienceDevTableBase(_TableMixin, AbstractConcreteBase, DataScienceDevBase):
    """Table with Integer primary key."""

    __abstract__ = True

    id: Mapped[int] = mapped_column(primary_key=True)


class DataScienceDevTableBaseBig(_TableMixin, AbstractConcreteBase, DataScienceDevBase):
    """Table with BigInteger primary key."""

    __abstract__ = True

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

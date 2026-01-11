"""Base ORM definitions."""

from __future__ import annotations

from datetime import datetime
from os import getenv
from typing import cast

from sqlalchemy import DateTime, MetaData, create_engine, func
from sqlalchemy.engine import URL, Engine
from sqlalchemy.ext.declarative import AbstractConcreteBase
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class RichieBase(DeclarativeBase):
    """Base class for all ORM models."""

    schema_name = "main"

    metadata = MetaData(
        schema=schema_name,
        naming_convention={
            "ix": "ix_%(table_name)s_%(column_0_name)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        },
    )


class TableBase(AbstractConcreteBase, RichieBase):
    """Abstract concrete base for tables with IDs and timestamps."""

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


def get_connection_info() -> tuple[str, str, str, str, str | None]:
    """Get connection info from environment variables."""
    database = getenv("POSTGRES_DB")
    host = getenv("POSTGRES_HOST")
    port = getenv("POSTGRES_PORT")
    username = getenv("POSTGRES_USER")
    password = getenv("POSTGRES_PASSWORD")

    if None in (database, host, port, username):
        error = (
            "Missing environment variables for Postgres connection.\n"
            f"{database=}\n"
            f"{host=}\n"
            f"{port=}\n"
            f"{username=}\n"
            f"password{'***' if password else None}\n"
        )
        raise ValueError(error)
    return cast("tuple[str, str, str, str, str | None]", (database, host, port, username, password))


def get_postgres_engine(*, pool_pre_ping: bool = True) -> Engine:
    """Create a SQLAlchemy engine from environment variables."""
    database, host, port, username, password = get_connection_info()

    url = URL.create(
        drivername="postgresql+psycopg",
        username=username,
        password=password,
        host=host,
        port=int(port),
        database=database,
    )

    return create_engine(
        url=url,
        pool_pre_ping=pool_pre_ping,
        pool_recycle=1800,
    )

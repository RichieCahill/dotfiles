"""Shared ORM definitions."""

from __future__ import annotations

from os import getenv
from typing import cast

from sqlalchemy import create_engine
from sqlalchemy.engine import URL, Engine

NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_name)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


def get_connection_info(name: str) -> tuple[str, str, str, str, str | None]:
    """Get connection info from environment variables."""
    database = getenv(f"{name}_DB")
    host = getenv(f"{name}_HOST")
    port = getenv(f"{name}_PORT")
    username = getenv(f"{name}_USER")
    password = getenv(f"{name}_PASSWORD")

    if None in (database, host, port, username):
        error = f"Missing environment variables for Postgres connection.\n{database=}\n{host=}\n{port=}\n{username=}\n"
        raise ValueError(error)
    return cast("tuple[str, str, str, str, str | None]", (database, host, port, username, password))


def get_postgres_engine(*, name: str = "POSTGRES", pool_pre_ping: bool = True) -> Engine:
    """Create a SQLAlchemy engine from environment variables."""
    database, host, port, username, password = get_connection_info(name)

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

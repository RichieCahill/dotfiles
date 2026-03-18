"""Shared test fixtures."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from sqlalchemy import create_engine, event

from python.orm.signal_bot.base import SignalBotBase

if TYPE_CHECKING:
    from collections.abc import Generator

    from sqlalchemy.engine import Engine


@pytest.fixture(scope="session")
def sqlite_engine() -> Generator[Engine]:
    """Create an in-memory SQLite engine for testing."""
    engine = create_engine("sqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    SignalBotBase.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def engine(sqlite_engine: Engine) -> Generator[Engine]:
    """Yield the shared engine after cleaning all tables between tests."""
    yield sqlite_engine
    with sqlite_engine.begin() as connection:
        for table in reversed(SignalBotBase.metadata.sorted_tables):
            connection.execute(table.delete())

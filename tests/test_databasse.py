"""test_database."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from sqlalchemy import Integer, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from python.database import safe_insert

if TYPE_CHECKING:
    from collections.abc import Generator


class TestingBase(DeclarativeBase):
    """TestingBase."""


class Item(TestingBase):
    """Item."""

    __tablename__ = "items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)


@pytest.fixture
def session() -> Generator[Session]:
    """Fresh in-memory DB + tables for each test."""
    engine = create_engine("sqlite+pysqlite:///:memory:", echo=False, future=True)
    TestingBase.metadata.create_all(engine)
    with sessionmaker(bind=engine, expire_on_commit=False, future=True)() as s:
        yield s


def test_partial_failure_unique_constraint(session: Session) -> None:
    """Duplicate name should fail only for the conflicting row; others commit."""
    objs = [Item(name="a"), Item(name="b"), Item(name="a"), Item(name="c")]
    failures = safe_insert(objs, session)

    assert len(failures) == 1
    exc, failed_obj = failures[0]
    assert isinstance(exc, Exception)
    assert isinstance(failed_obj, Item)
    assert failed_obj.name == "a"

    rows = session.scalars(select(Item.name)).all()
    assert sorted(rows) == ["a", "b", "c"]
    assert rows.count("a") == 1


def test_all_good_inserts(session: Session) -> None:
    """No failures when all rows are valid."""
    objs = [Item(name="x"), Item(name="y")]
    failures = safe_insert(objs, session)
    assert failures == []

    rows = session.scalars(select(Item.name).where(Item.name.in_(("x", "y")))).all()
    assert sorted(rows) == ["x", "y"]


def test_unmapped_object_raises(session: Session) -> None:
    """Non-ORM instances should raise TypeError immediately."""
    with pytest.raises(TypeError):
        safe_insert([object()], session)

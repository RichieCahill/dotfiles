"""Dynamically generated ORM classes for each weekly partition of the posts table.

Each class maps to a PostgreSQL partition table (e.g. posts_2024_01).
These are real ORM models tracked by Alembic autogenerate.

Uses ISO week numbering (datetime.isocalendar().week). ISO years can have
52 or 53 weeks, and week boundaries are always Monday to Monday.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime

from python.orm.data_science_dev.base import DataScienceDevBase
from python.orm.data_science_dev.posts.columns import PostsColumns

PARTITION_START_YEAR = 2024
PARTITION_END_YEAR = 2025

_current_module = sys.modules[__name__]


def iso_weeks_in_year(year: int) -> int:
    """Return the number of ISO weeks in a given year (52 or 53)."""
    dec_28 = datetime(year, 12, 28, tzinfo=UTC)
    return dec_28.isocalendar().week


def week_bounds(year: int, week: int) -> tuple[datetime, datetime]:
    """Return (start, end) datetimes for an ISO week.

    Start = Monday 00:00:00 UTC of the given ISO week.
    End   = Monday 00:00:00 UTC of the following ISO week.
    """
    start = datetime.fromisocalendar(year, week, 1).replace(tzinfo=UTC)
    if week < iso_weeks_in_year(year):
        end = datetime.fromisocalendar(year, week + 1, 1).replace(tzinfo=UTC)
    else:
        end = datetime.fromisocalendar(year + 1, 1, 1).replace(tzinfo=UTC)
    return start, end


def _build_partition_classes() -> dict[str, type]:
    """Generate one ORM class per ISO week partition."""
    classes: dict[str, type] = {}

    for year in range(PARTITION_START_YEAR, PARTITION_END_YEAR + 1):
        for week in range(1, iso_weeks_in_year(year) + 1):
            class_name = f"PostsWeek{year}W{week:02d}"
            table_name = f"posts_{year}_{week:02d}"

            partition_class = type(
                class_name,
                (PostsColumns, DataScienceDevBase),
                {
                    "__tablename__": table_name,
                    "__table_args__": ({"implicit_returning": False},),
                },
            )

            classes[class_name] = partition_class

    return classes


# Generate all partition classes and register them on this module
_partition_classes = _build_partition_classes()
for _name, _cls in _partition_classes.items():
    setattr(_current_module, _name, _cls)
__all__ = list(_partition_classes.keys())

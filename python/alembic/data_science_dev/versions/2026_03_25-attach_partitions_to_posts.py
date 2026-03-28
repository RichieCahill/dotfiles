"""Attach all partition tables to the posts parent table.

Alembic autogenerate creates partition tables as standalone tables but does not
emit the ALTER TABLE ... ATTACH PARTITION statements needed for PostgreSQL to
route inserts to the correct partition.

Revision ID: a1b2c3d4e5f6
Revises: 605b1794838f
Create Date: 2026-03-25 10:00:00.000000

"""

from __future__ import annotations

from typing import TYPE_CHECKING

from alembic import op
from sqlalchemy import text

from python.orm import DataScienceDevBase
from python.orm.data_science_dev.posts.partitions import (
    PARTITION_END_YEAR,
    PARTITION_START_YEAR,
    iso_weeks_in_year,
    week_bounds,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "605b1794838f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

schema = DataScienceDevBase.schema_name

ALREADY_ATTACHED_QUERY = text("""
    SELECT inhrelid::regclass::text
    FROM pg_inherits
    WHERE inhparent = :parent::regclass
""")


def upgrade() -> None:
    """Attach all weekly partition tables to the posts parent table."""
    connection = op.get_bind()
    already_attached = {row[0] for row in connection.execute(ALREADY_ATTACHED_QUERY, {"parent": f"{schema}.posts"})}

    for year in range(PARTITION_START_YEAR, PARTITION_END_YEAR + 1):
        for week in range(1, iso_weeks_in_year(year) + 1):
            table_name = f"posts_{year}_{week:02d}"
            qualified_name = f"{schema}.{table_name}"
            if qualified_name in already_attached:
                continue
            start, end = week_bounds(year, week)
            start_str = start.strftime("%Y-%m-%d %H:%M:%S")
            end_str = end.strftime("%Y-%m-%d %H:%M:%S")
            op.execute(
                f"ALTER TABLE {schema}.posts "
                f"ATTACH PARTITION {qualified_name} "
                f"FOR VALUES FROM ('{start_str}') TO ('{end_str}')"
            )


def downgrade() -> None:
    """Detach all weekly partition tables from the posts parent table."""
    for year in range(PARTITION_START_YEAR, PARTITION_END_YEAR + 1):
        for week in range(1, iso_weeks_in_year(year) + 1):
            table_name = f"posts_{year}_{week:02d}"
            op.execute(f"ALTER TABLE {schema}.posts DETACH PARTITION {schema}.{table_name}")

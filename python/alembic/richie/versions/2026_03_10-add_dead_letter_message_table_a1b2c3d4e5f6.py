"""add dead_letter_message table.

Revision ID: a1b2c3d4e5f6
Revises: 99fec682516c
Create Date: 2026-03-10 12:00:00.000000

"""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from python.orm import RichieBase

if TYPE_CHECKING:
    from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "99fec682516c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

schema = RichieBase.schema_name


def upgrade() -> None:
    """Upgrade."""
    op.create_table(
        "dead_letter_message",
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM("UNPROCESSED", "PROCESSED", name="message_status", schema=schema),
            nullable=False,
        ),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_dead_letter_message")),
        schema=schema,
    )


def downgrade() -> None:
    """Downgrade."""
    op.drop_table("dead_letter_message", schema=schema)
    op.execute(sa.text(f"DROP TYPE IF EXISTS {schema}.message_status"))

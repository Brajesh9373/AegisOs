"""Event-store table.

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-06 00:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_event_store"
down_revision: str | None = "0002_aggregates"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the append-only event_store table."""
    op.create_table(
        "event_store",
        sa.Column(
            "sequence",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column("event_id", sa.String(length=128), nullable=False),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("event_category", sa.String(length=32), nullable=False),
        sa.Column("correlation_id", sa.String(length=128), nullable=True),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_event_store_event_id", "event_store", ["event_id"])
    op.create_index("ix_event_store_event_type", "event_store", ["event_type"])
    op.create_index("ix_event_store_event_category", "event_store", ["event_category"])
    op.create_index("ix_event_store_correlation_id", "event_store", ["correlation_id"])
    op.create_index("ix_event_store_created_at", "event_store", ["created_at"])


def downgrade() -> None:
    """Drop the event_store table."""
    op.drop_index("ix_event_store_created_at", table_name="event_store")
    op.drop_index("ix_event_store_correlation_id", table_name="event_store")
    op.drop_index("ix_event_store_event_category", table_name="event_store")
    op.drop_index("ix_event_store_event_type", table_name="event_store")
    op.drop_index("ix_event_store_event_id", table_name="event_store")
    op.drop_table("event_store")

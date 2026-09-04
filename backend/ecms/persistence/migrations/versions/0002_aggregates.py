"""Aggregate document store table.

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-06 00:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_aggregates"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the aggregates table."""
    op.create_table(
        "aggregates",
        sa.Column("id", sa.String(length=128), primary_key=True),
        sa.Column("aggregate_type", sa.String(length=128), nullable=False),
        sa.Column("organization_id", sa.String(length=128), nullable=True),
        sa.Column("workspace_id", sa.String(length=128), nullable=True),
        sa.Column("project_id", sa.String(length=128), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("lifecycle_state", sa.String(length=32), nullable=False),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_aggregates_aggregate_type", "aggregates", ["aggregate_type"])
    op.create_index("ix_aggregates_organization_id", "aggregates", ["organization_id"])
    op.create_index("ix_aggregates_lifecycle_state", "aggregates", ["lifecycle_state"])


def downgrade() -> None:
    """Drop the aggregates table."""
    op.drop_index("ix_aggregates_lifecycle_state", table_name="aggregates")
    op.drop_index("ix_aggregates_organization_id", table_name="aggregates")
    op.drop_index("ix_aggregates_aggregate_type", table_name="aggregates")
    op.drop_table("aggregates")

"""Initial audit records table.

Revision ID: 0001
Revises:
Create Date: 2026-07-06 00:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the audit_records table."""
    op.create_table(
        "audit_records",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("actor", sa.String(length=255), nullable=False),
        sa.Column("action", sa.String(length=255), nullable=False),
        sa.Column("resource", sa.String(length=255), nullable=False),
        sa.Column("outcome", sa.String(length=32), nullable=False),
        sa.Column("details", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_audit_records_actor", "audit_records", ["actor"])
    op.create_index("ix_audit_records_action", "audit_records", ["action"])
    op.create_index("ix_audit_records_created_at", "audit_records", ["created_at"])


def downgrade() -> None:
    """Drop the audit_records table."""
    op.drop_index("ix_audit_records_created_at", table_name="audit_records")
    op.drop_index("ix_audit_records_action", table_name="audit_records")
    op.drop_index("ix_audit_records_actor", table_name="audit_records")
    op.drop_table("audit_records")

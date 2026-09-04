"""SessionContext KV table.

Revision ID: 0006
Revises: 0005
Create Date: 2026-07-11 00:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006_session_context"
down_revision: str | None = "0005_sessions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "session_context",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.String(length=128), nullable=False),
        sa.Column("key", sa.String(length=255), nullable=False),
        sa.Column("value", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_session_context_session_id", "session_context", ["session_id"])
    op.create_index("ix_session_context_session_key", "session_context", ["session_id", "key"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_session_context_session_key", table_name="session_context")
    op.drop_index("ix_session_context_session_id", table_name="session_context")
    op.drop_table("session_context")

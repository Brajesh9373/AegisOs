"""Notification schema compatibility.

Revision ID: 0028
Revises: 0027
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0028"
down_revision: str | None = "0027"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS notifications (
            id TEXT PRIMARY KEY,
            project_id TEXT,
            meeting_id TEXT,
            type TEXT,
            title TEXT,
            message TEXT,
            status TEXT DEFAULT 'unread',
            action_type TEXT,
            action_data JSONB DEFAULT '{}',
            created_at TEXT,
            updated_at TEXT
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_notifications_project_id ON notifications (project_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_notifications_status ON notifications (project_id, status)")


def downgrade() -> None:
    pass

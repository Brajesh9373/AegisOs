"""Project meetings: calendar, notes, decisions, and recordings.

Adds a project-scoped `meetings` table backing the Meetings tab. Each row is one
meeting with its notes, decisions/action items (JSON arrays), participants, and an
optional recording file path (recordings are stored on local disk, reusing the
project upload directory convention).

Revision ID: 0024
Revises: 0023
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0024_meetings"
down_revision: str | None = "0023_user_name_column"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS meetings (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            title TEXT NOT NULL,
            meeting_date TEXT,
            meeting_time TEXT,
            duration TEXT,
            type TEXT DEFAULT 'both',
            status TEXT DEFAULT 'upcoming',
            participants JSONB DEFAULT '[]',
            agenda TEXT,
            notes TEXT,
            summary TEXT,
            decisions JSONB DEFAULT '[]',
            action_items JSONB DEFAULT '[]',
            attachments JSONB DEFAULT '[]',
            recording_path TEXT,
            recording_name TEXT,
            source TEXT DEFAULT 'manual',
            created_at TEXT,
            updated_at TEXT
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_meetings_project_id ON meetings (project_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_meetings_date ON meetings (project_id, meeting_date)")


def downgrade() -> None:
    pass

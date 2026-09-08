"""Production requirements storage — 3 tables + JSONB column.

Revision ID: 0020
Revises: 0019
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
from ecms.persistence.migrations.compat import add_column_if_missing

revision: str = "0020_requirements_tables"
down_revision: str | None = "0019_agent_task_progress"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    add_column_if_missing("business_projects", "requirements JSONB")

    op.execute("""
        CREATE TABLE IF NOT EXISTS project_requirements (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL REFERENCES business_projects(id) ON DELETE CASCADE,
            text TEXT NOT NULL,
            type TEXT DEFAULT 'general',
            status TEXT DEFAULT 'confirmed',
            source TEXT,
            version INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS project_constraints (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL REFERENCES business_projects(id) ON DELETE CASCADE,
            type TEXT NOT NULL,
            value TEXT NOT NULL,
            mandatory BOOLEAN DEFAULT false,
            source TEXT,
            version INTEGER DEFAULT 1,
            created_at TEXT NOT NULL
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS project_risks (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL REFERENCES business_projects(id) ON DELETE CASCADE,
            risk TEXT NOT NULL,
            impact TEXT NOT NULL,
            mitigation TEXT,
            status TEXT DEFAULT 'open',
            version INTEGER DEFAULT 1,
            created_at TEXT NOT NULL
        )
    """)


def downgrade() -> None:
    pass

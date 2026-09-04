"""Add project work-board tables.

Revision ID: 0027
Revises: 0026
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0027_project_work_items"
down_revision: str | None = "0026_platform_schema_compat"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS project_epics (
            id          TEXT PRIMARY KEY,
            project_id  TEXT NOT NULL REFERENCES business_projects(id) ON DELETE CASCADE,
            title       TEXT NOT NULL,
            description TEXT,
            status      TEXT NOT NULL DEFAULT 'TO_DO',
            sort_order  INTEGER NOT NULL DEFAULT 0,
            created_at  TEXT NOT NULL,
            updated_at  TEXT NOT NULL
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS project_stories (
            id           TEXT PRIMARY KEY,
            project_id   TEXT NOT NULL REFERENCES business_projects(id) ON DELETE CASCADE,
            epic_id      TEXT REFERENCES project_epics(id) ON DELETE CASCADE,
            title        TEXT NOT NULL,
            description  TEXT,
            status       TEXT NOT NULL DEFAULT 'TO_DO',
            assignee_id  TEXT,
            story_points INTEGER,
            sort_order   INTEGER NOT NULL DEFAULT 0,
            created_at   TEXT NOT NULL,
            updated_at   TEXT NOT NULL
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS project_story_bugs (
            id          TEXT PRIMARY KEY,
            project_id  TEXT NOT NULL REFERENCES business_projects(id) ON DELETE CASCADE,
            story_id    TEXT NOT NULL REFERENCES project_stories(id) ON DELETE CASCADE,
            title       TEXT NOT NULL,
            description TEXT,
            severity    TEXT NOT NULL DEFAULT 'Medium',
            status      TEXT NOT NULL DEFAULT 'TO_DO',
            sort_order  INTEGER NOT NULL DEFAULT 0,
            created_at  TEXT NOT NULL,
            updated_at  TEXT NOT NULL
        )
    """)

    op.execute("CREATE INDEX IF NOT EXISTS idx_project_epics_project ON project_epics(project_id)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_project_stories_project ON project_stories(project_id)"
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_project_stories_epic ON project_stories(epic_id)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_project_story_bugs_project ON project_story_bugs(project_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_project_story_bugs_story ON project_story_bugs(story_id)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS project_story_bugs")
    op.execute("DROP TABLE IF EXISTS project_stories")
    op.execute("DROP TABLE IF EXISTS project_epics")

"""Platform tables: artifacts and audit_logs.

Revision ID: 0014
Revises: 0013
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0014_platform_artifacts_audit"
down_revision: str | None = "0013_platform_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS artifacts (
            id              TEXT PRIMARY KEY,
            projectId       TEXT,
            name            TEXT NOT NULL,
            type            TEXT NOT NULL,
            content         TEXT,
            uri             TEXT,
            agentId         TEXT,
            createdAt       TEXT
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id              TEXT PRIMARY KEY,
            projectId       TEXT,
            userId          TEXT,
            action          TEXT NOT NULL,
            detail          TEXT,
            createdAt       TEXT
        )
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS audit_logs")
    op.execute("DROP TABLE IF EXISTS artifacts")

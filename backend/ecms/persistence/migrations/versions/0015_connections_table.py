"""Connections table for tracking user sync connections.

Revision ID: 0015
Revises: 0014
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0015"
down_revision: str | None = "0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS connections (
            number       SERIAL PRIMARY KEY,
            user_id      TEXT NOT NULL,
            name         TEXT NOT NULL,
            provider     TEXT NOT NULL,
            repo_url     TEXT,
            config       TEXT DEFAULT '{}',
            status       TEXT DEFAULT 'syncing',
            node_count   INTEGER DEFAULT 0,
            created_at   TEXT NOT NULL,
            updated_at   TEXT NOT NULL
        )
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS connections")

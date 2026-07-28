"""AI model configs table.

Revision ID: 0016
Revises: 0015
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0016"
down_revision: str | None = "0015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS ai_models (
            id              TEXT PRIMARY KEY,
            name            TEXT NOT NULL,
            provider        TEXT NOT NULL,
            model_id        TEXT NOT NULL,
            api_key         TEXT,
            base_url        TEXT,
            is_default      INTEGER DEFAULT 0,
            created_at      TEXT NOT NULL
        )
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS ai_models")

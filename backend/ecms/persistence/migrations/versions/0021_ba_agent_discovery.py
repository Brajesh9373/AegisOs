"""BA agent: is_ba_agent flag on ai_models + discovery_sessions table.

Revision ID: 0021
Revises: 0020
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0021_ba_agent_discovery"
down_revision: str | None = "0020_requirements_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Add is_ba_agent singleton flag to ai_models (mirrors is_default pattern).
    op.execute("ALTER TABLE ai_models ADD COLUMN is_ba_agent INTEGER DEFAULT 0")

    # 2. Discovery sessions — persists the BA agent state machine per project.
    op.execute("""
        CREATE TABLE IF NOT EXISTS discovery_sessions (
            id              TEXT PRIMARY KEY,
            project_id      TEXT,
            stage           TEXT NOT NULL DEFAULT 'DRAFT',
            source_text     TEXT,
            transcript      TEXT,
            messages        JSONB DEFAULT '[]',
            requirements    JSONB,
            ai_model_id     TEXT,
            created_at      TEXT NOT NULL,
            updated_at      TEXT NOT NULL
        )
    """)


def downgrade() -> None:
    pass

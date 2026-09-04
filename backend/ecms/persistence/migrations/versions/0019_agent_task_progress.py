"""Add show_task_progress column to agents table.

Revision ID: 0019
Revises: 0018
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0019_agent_task_progress"
down_revision: str | None = "0018_org_support"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE agents ADD COLUMN IF NOT EXISTS show_task_progress INTEGER DEFAULT 1")


def downgrade() -> None:
    pass

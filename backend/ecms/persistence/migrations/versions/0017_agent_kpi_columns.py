"""Agent KPI and connector columns.

Revision ID: 0017
Revises: 0016
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0017_agent_kpi_columns"
down_revision: str | None = "0016_ai_models_table"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE agents ADD COLUMN IF NOT EXISTS connector_type TEXT")
    op.execute("ALTER TABLE agents ADD COLUMN IF NOT EXISTS execution_count INTEGER DEFAULT 0")
    op.execute("ALTER TABLE agents ADD COLUMN IF NOT EXISTS last_active_at TEXT")
    op.execute("ALTER TABLE agents ADD COLUMN IF NOT EXISTS error_count_30d INTEGER DEFAULT 0")
    op.execute("ALTER TABLE agents ADD COLUMN IF NOT EXISTS active_workspaces INTEGER DEFAULT 0")
    op.execute("ALTER TABLE agents ADD COLUMN IF NOT EXISTS certificates JSON DEFAULT '[]'")


def downgrade() -> None:
    pass

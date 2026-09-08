"""Agent KPI and connector columns.

Revision ID: 0017
Revises: 0016
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
from ecms.persistence.migrations.compat import add_column_if_missing

revision: str = "0017_agent_kpi_columns"
down_revision: str | None = "0016_ai_models_table"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    add_column_if_missing("agents", "connector_type TEXT")
    add_column_if_missing("agents", "execution_count INTEGER DEFAULT 0")
    add_column_if_missing("agents", "last_active_at TEXT")
    add_column_if_missing("agents", "error_count_30d INTEGER DEFAULT 0")
    add_column_if_missing("agents", "active_workspaces INTEGER DEFAULT 0")
    add_column_if_missing("agents", "certificates JSON DEFAULT '[]'")


def downgrade() -> None:
    pass

"""Multi-org support — add organization_id to projects, agents, connections.

Revision ID: 0018
Revises: 0017
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
from ecms.persistence.migrations.compat import add_column_if_missing

revision: str = "0018_org_support"
down_revision: str | None = "0017_agent_kpi_columns"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    add_column_if_missing("business_projects", "organization_id TEXT")
    add_column_if_missing("agents", "organization_id TEXT")
    add_column_if_missing("connections", "project_id TEXT")


def downgrade() -> None:
    pass

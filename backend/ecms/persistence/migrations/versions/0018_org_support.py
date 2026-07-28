"""Multi-org support — add organization_id to projects, agents, connections.

Revision ID: 0018
Revises: 0017
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0018"
down_revision: str | None = "0017"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE business_projects ADD COLUMN IF NOT EXISTS organization_id TEXT")
    op.execute("ALTER TABLE agents ADD COLUMN IF NOT EXISTS organization_id TEXT")
    op.execute("ALTER TABLE connections ADD COLUMN IF NOT EXISTS project_id TEXT")


def downgrade() -> None:
    pass

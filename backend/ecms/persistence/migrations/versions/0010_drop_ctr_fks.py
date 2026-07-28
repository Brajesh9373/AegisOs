"""Add policy_recommendations, drop FK constraint.

Revision ID: 0010
Revises: 0009
Create Date: 2026-07-11 00:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE policy_recommendations DROP CONSTRAINT IF EXISTS policy_recommendations_project_id_fkey")
    op.execute("ALTER TABLE policy_recommendations DROP CONSTRAINT IF EXISTS policy_recommendations_reviewed_by_fkey")


def downgrade() -> None:
    pass

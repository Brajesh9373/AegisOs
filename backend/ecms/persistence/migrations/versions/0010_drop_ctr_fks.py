"""Add policy_recommendations, drop FK constraint.

Revision ID: 0010
Revises: 0009
Create Date: 2026-07-11 00:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

from ecms.persistence.migrations.compat import drop_constraint_if_exists

revision: str = "0010_drop_ctr_fks"
down_revision: str | None = "0009_access_policies"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    drop_constraint_if_exists(
        "policy_recommendations", "policy_recommendations_project_id_fkey"
    )
    drop_constraint_if_exists(
        "policy_recommendations", "policy_recommendations_reviewed_by_fkey"
    )


def downgrade() -> None:
    pass

"""Seed organization_members from permanent agent records.

Copies agents WHERE project_id IS NULL into the new organization_members table,
preserving IDs so existing references remain valid.

Revision ID: 0030
Revises: 0029
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0030"
down_revision: str | None = "0029"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Copy permanent agents (project_id IS NULL) into organization_members."""
    op.execute(
        """
        INSERT INTO organization_members
            (id, name, designation, role, department, role_description, skills,
             reports_to, status, created_at, updated_at)
        SELECT
            id, name, designation, role, department, role_description, skills,
            reports_to, status, created_at, updated_at
        FROM agents
        WHERE project_id IS NULL
        ON CONFLICT (id) DO NOTHING
        """
    )


def downgrade() -> None:
    """Remove seeded records (only those that match agent IDs)."""
    op.execute(
        """
        DELETE FROM organization_members
        WHERE id IN (SELECT id FROM agents WHERE project_id IS NULL)
        """
    )

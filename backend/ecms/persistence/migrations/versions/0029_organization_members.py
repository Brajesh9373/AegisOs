"""Organization members and governance assignments.

Revision ID: 0029
Revises: 0028
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0029_organization_members"
down_revision: str | None = "0028_notifications_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── organization_members ──────────────────────────────────────────
    op.create_table(
        "organization_members",
        sa.Column("id", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("designation", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("role", sa.String(length=64), nullable=False),
        sa.Column("department", sa.String(length=128), nullable=False),
        sa.Column("role_description", sa.Text(), nullable=True),
        sa.Column("skills", sa.JSON(), nullable=True),
        sa.Column("reports_to", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("user_id", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["reports_to"],
            ["organization_members.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_organization_members_role", "organization_members", ["role"])
    op.create_index("ix_organization_members_department", "organization_members", ["department"])
    op.create_index("ix_organization_members_reports_to", "organization_members", ["reports_to"])
    op.create_index("ix_organization_members_status", "organization_members", ["status"])

    # ── project_agent_governance_assignments ──────────────────────────
    op.create_table(
        "project_agent_governance_assignments",
        sa.Column("id", sa.String(length=128), nullable=False),
        sa.Column("organization_member_id", sa.String(length=128), nullable=False),
        sa.Column("project_agent_id", sa.String(length=128), nullable=False),
        sa.Column("project_id", sa.String(length=128), nullable=False),
        sa.Column("responsibility", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("assigned_by_user_id", sa.String(length=128), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("review_reason", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["organization_member_id"],
            ["organization_members.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["project_agent_id"],
            ["agents.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_member_id",
            "project_agent_id",
            "responsibility",
            name="uq_member_agent_responsibility",
        ),
    )
    op.create_index(
        "ix_gov_assignments_member_id",
        "project_agent_governance_assignments",
        ["organization_member_id"],
    )
    op.create_index(
        "ix_gov_assignments_agent_id",
        "project_agent_governance_assignments",
        ["project_agent_id"],
    )
    op.create_index(
        "ix_gov_assignments_project_id",
        "project_agent_governance_assignments",
        ["project_id"],
    )
    op.create_index(
        "ix_gov_assignments_responsibility",
        "project_agent_governance_assignments",
        ["responsibility"],
    )
    op.create_index(
        "ix_gov_assignments_status",
        "project_agent_governance_assignments",
        ["status"],
    )


def downgrade() -> None:
    op.drop_table("project_agent_governance_assignments")
    op.drop_table("organization_members")

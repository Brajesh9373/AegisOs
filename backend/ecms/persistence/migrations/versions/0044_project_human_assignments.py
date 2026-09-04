"""Project human owner/oversight assignments.

Revision ID: 0044
Revises: 0043
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0044_project_human_assignments"
down_revision: str | None = "0043_project_agent_positions"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "project_human_assignments",
        sa.Column("id", sa.String(length=128), primary_key=True),
        sa.Column("project_id", sa.String(length=128), nullable=False),
        sa.Column("organization_member_id", sa.String(length=128), nullable=False),
        sa.Column("position_id", sa.String(length=128), nullable=True),
        sa.Column("scope", sa.String(length=64), nullable=False),
        sa.Column("responsibility", sa.String(length=64), nullable=False, server_default="workspace_owner"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("assigned_by_user_id", sa.String(length=128), nullable=True),
        sa.Column("source", sa.String(length=64), nullable=False, server_default="system"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["organization_member_id"], ["organization_members.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["position_id"], ["project_agent_positions.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("project_id", "scope", "position_id", "organization_member_id", name="uq_project_human_assignment"),
    )
    op.create_index("ix_project_human_assignments_project_id", "project_human_assignments", ["project_id"])
    op.create_index("ix_project_human_assignments_member_id", "project_human_assignments", ["organization_member_id"])
    op.create_index("ix_project_human_assignments_position_id", "project_human_assignments", ["position_id"])
    op.create_index("ix_project_human_assignments_scope", "project_human_assignments", ["scope"])
    op.create_index("ix_project_human_assignments_status", "project_human_assignments", ["status"])
    op.create_index(
        "uq_project_workspace_owner_active",
        "project_human_assignments",
        ["project_id"],
        unique=True,
        postgresql_where=sa.text("scope = 'workspace_owner' AND status = 'active'"),
    )


def downgrade() -> None:
    op.drop_index("uq_project_workspace_owner_active", table_name="project_human_assignments")
    op.drop_index("ix_project_human_assignments_status", table_name="project_human_assignments")
    op.drop_index("ix_project_human_assignments_scope", table_name="project_human_assignments")
    op.drop_index("ix_project_human_assignments_position_id", table_name="project_human_assignments")
    op.drop_index("ix_project_human_assignments_member_id", table_name="project_human_assignments")
    op.drop_index("ix_project_human_assignments_project_id", table_name="project_human_assignments")
    op.drop_table("project_human_assignments")

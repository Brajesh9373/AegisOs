"""Project agent positions and reusable assignments.

Revision ID: 0043
Revises: 0042
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0043"
down_revision: str | None = "0042"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "project_agent_positions",
        sa.Column("id", sa.String(length=128), primary_key=True),
        sa.Column("project_id", sa.String(length=128), nullable=False),
        sa.Column("position_key", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=128), nullable=False),
        sa.Column("designation", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("role_description", sa.Text(), nullable=True),
        sa.Column("skills", sa.JSON(), nullable=True),
        sa.Column("department", sa.String(length=128), nullable=False),
        sa.Column("reports_to", sa.String(length=128), nullable=True),
        sa.Column("model", sa.String(length=255), nullable=True),
        sa.Column("tool_policy", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("system_prompt_addon", sa.Text(), nullable=True),
        sa.Column("automation", sa.JSON(), nullable=True),
        sa.Column("features", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["reports_to"], ["project_agent_positions.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("project_id", "position_key", name="uq_project_agent_position_key"),
    )
    op.create_index("ix_project_agent_positions_project_id", "project_agent_positions", ["project_id"])
    op.create_index("ix_project_agent_positions_role", "project_agent_positions", ["role"])
    op.create_index("ix_project_agent_positions_designation", "project_agent_positions", ["designation"])
    op.create_index("ix_project_agent_positions_department", "project_agent_positions", ["department"])
    op.create_index("ix_project_agent_positions_reports_to", "project_agent_positions", ["reports_to"])
    op.create_index("ix_project_agent_positions_status", "project_agent_positions", ["status"])

    op.create_table(
        "project_agent_assignments",
        sa.Column("position_id", sa.String(length=128), primary_key=True),
        sa.Column("agent_id", sa.String(length=128), nullable=False),
        sa.Column("assigned_by_user_id", sa.String(length=128), nullable=True),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["position_id"], ["project_agent_positions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_project_agent_assignments_agent_id", "project_agent_assignments", ["agent_id"])


def downgrade() -> None:
    op.drop_index("ix_project_agent_assignments_agent_id", table_name="project_agent_assignments")
    op.drop_table("project_agent_assignments")
    op.drop_index("ix_project_agent_positions_status", table_name="project_agent_positions")
    op.drop_index("ix_project_agent_positions_reports_to", table_name="project_agent_positions")
    op.drop_index("ix_project_agent_positions_department", table_name="project_agent_positions")
    op.drop_index("ix_project_agent_positions_designation", table_name="project_agent_positions")
    op.drop_index("ix_project_agent_positions_role", table_name="project_agent_positions")
    op.drop_index("ix_project_agent_positions_project_id", table_name="project_agent_positions")
    op.drop_table("project_agent_positions")

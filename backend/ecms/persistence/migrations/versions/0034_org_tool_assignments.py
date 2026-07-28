"""Create org_tool_assignments table.

Maps organization members to tools (Jira, GitHub, AWS, etc.)
so each tool in the admin Tools tab can be assigned to a human owner.

Revision ID: 0034
Revises: 0033
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0034"
down_revision: str | None = "0033"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "org_tool_assignments",
        sa.Column("id", sa.String(128), primary_key=True),
        sa.Column("organization_member_id", sa.String(128), nullable=False),
        sa.Column("tool_name", sa.String(64), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_org_tool_assignments_member", "org_tool_assignments", ["organization_member_id"])
    op.create_index("ix_org_tool_assignments_tool", "org_tool_assignments", ["tool_name"])
    op.create_unique_constraint(
        "uq_org_tool_member_tool",
        "org_tool_assignments",
        ["organization_member_id", "tool_name"],
    )


def downgrade() -> None:
    op.drop_table("org_tool_assignments")

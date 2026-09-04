"""Access policies and policy recommendations.

Revision ID: 0009
Revises: 0008
Create Date: 2026-07-11 00:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009_access_policies"
down_revision: str | None = "0008_agent_skills"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "access_policies",
        sa.Column("id", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("effect", sa.String(length=16), nullable=False),
        sa.Column("agent_id", sa.String(length=128), nullable=True),
        sa.Column("department", sa.String(length=128), nullable=True),
        sa.Column("role_level_min", sa.Integer(), nullable=True, server_default="1"),
        sa.Column("resource_type", sa.String(length=32), nullable=True),
        sa.Column("path_pattern", sa.String(length=512), nullable=True),
        sa.Column("source_type", sa.String(length=64), nullable=True),
        sa.Column("resource_attrs", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("action", sa.String(length=16), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("created_by", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["agents.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_access_policies_agent_id", "access_policies", ["agent_id"])
    op.create_index("ix_access_policies_department", "access_policies", ["department"])

    op.create_table(
        "policy_recommendations",
        sa.Column("id", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("project_id", sa.String(length=128), nullable=True),
        sa.Column("policies_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("org_snapshot", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("reviewed_by", sa.String(length=128), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["reviewed_by"], ["agents.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_policy_recommendations_project_id", "policy_recommendations", ["project_id"]
    )
    op.create_index("ix_policy_recommendations_status", "policy_recommendations", ["status"])


def downgrade() -> None:
    op.drop_index("ix_policy_recommendations_status", table_name="policy_recommendations")
    op.drop_index("ix_policy_recommendations_project_id", table_name="policy_recommendations")
    op.drop_table("policy_recommendations")
    op.drop_index("ix_access_policies_department", table_name="access_policies")
    op.drop_index("ix_access_policies_agent_id", table_name="access_policies")
    op.drop_table("access_policies")

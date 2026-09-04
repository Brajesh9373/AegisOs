"""Add agent_profiles table.

Revision ID: 0047_agent_profiles
Revises: 0046_ba_canonical_projections
Create Date: 2026-09-03

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0047_agent_profiles"
down_revision: str | None = "0046_ba_canonical_projections"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "agent_profiles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("profile_id", sa.String(64), nullable=False, index=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("version", sa.String(32), nullable=False, server_default="1.0.0"),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("role", sa.String(64), nullable=True),
        sa.Column("parent_profile_id", sa.String(64), nullable=True),
        sa.Column("system_prompt", sa.Text, nullable=True),
        sa.Column("user_prompt_template", sa.Text, nullable=True),
        sa.Column("stages", sa.JSON, nullable=True),
        sa.Column("memory_scope", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("knowledge_scope", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("tool_scope", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("scope_recommendations", sa.JSON, nullable=True),
        sa.Column("model_provider", sa.String(32), nullable=True),
        sa.Column("model_name", sa.String(64), nullable=True),
        sa.Column("temperature", sa.Float, nullable=True),
        sa.Column("max_tokens", sa.Integer, nullable=True),
        sa.Column("execution_budget", sa.JSON, nullable=True),
        sa.Column("created_by", sa.String(64), nullable=True),
        sa.Column(
            "createdat", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updatedat",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )
    op.create_index("ix_agent_profiles_status", "agent_profiles", ["status"])
    op.create_index("ix_agent_profiles_parent", "agent_profiles", ["parent_profile_id"])


def downgrade() -> None:
    op.drop_index("ix_agent_profiles_parent", "agent_profiles")
    op.drop_index("ix_agent_profiles_status", "agent_profiles")
    op.drop_table("agent_profiles")

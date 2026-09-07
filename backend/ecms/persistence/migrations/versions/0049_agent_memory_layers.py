"""Add agent_procedures, agent_preferences, and org_patterns tables.

Revision ID: 0049_agent_memory_layers
Revises: 0048_agent_episodes
Create Date: 2026-09-07

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0049_agent_memory_layers"
down_revision: str | None = "0048_agent_episodes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "agent_procedures",
        sa.Column("id", sa.String(128), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, index=True),
        sa.Column("description", sa.Text, nullable=False, server_default=""),
        sa.Column("steps", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("learned_by", sa.String(128), nullable=False, server_default=""),
        sa.Column("use_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )
    op.create_table(
        "agent_preferences",
        sa.Column("scope", sa.String(128), primary_key=True),
        sa.Column("key", sa.String(255), primary_key=True),
        sa.Column("value", sa.Text, nullable=False, server_default=""),
        sa.Column("updated_by", sa.String(128), nullable=False, server_default=""),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )
    op.create_table(
        "org_patterns",
        sa.Column("id", sa.String(128), primary_key=True),
        sa.Column("pattern_type", sa.String(32), nullable=False, index=True),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("published_by", sa.String(128), nullable=False, server_default=""),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_org_patterns_type", "org_patterns", ["pattern_type"])


def downgrade() -> None:
    op.drop_index("ix_org_patterns_type", "org_patterns")
    op.drop_table("org_patterns")
    op.drop_table("agent_preferences")
    op.drop_table("agent_procedures")

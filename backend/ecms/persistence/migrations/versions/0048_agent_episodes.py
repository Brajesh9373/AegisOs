"""Add agent_episodes table (durable agent memory).

Revision ID: 0048_agent_episodes
Revises: 0047_agent_profiles
Create Date: 2026-09-07

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0048_agent_episodes"
down_revision: str | None = "0047_agent_profiles"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "agent_episodes",
        sa.Column("uco_id", sa.String(128), primary_key=True),
        sa.Column("agent_id", sa.String(128), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=False, server_default=""),
        sa.Column("summary", sa.String(512), nullable=False, server_default=""),
        sa.Column(
            "ontology_type", sa.String(64), nullable=False, server_default="agent_episode"
        ),
        sa.Column("uco_json", sa.JSON, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_agent_episodes_agent_id", "agent_episodes", ["agent_id"])
    op.create_index("ix_agent_episodes_created_at", "agent_episodes", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_agent_episodes_created_at", "agent_episodes")
    op.drop_index("ix_agent_episodes_agent_id", "agent_episodes")
    op.drop_table("agent_episodes")

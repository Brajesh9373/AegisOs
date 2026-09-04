"""Add name column to users table.

Revision ID: 0023
Revises: 0022
"""

from __future__ import annotations

from alembic import op

revision = "0023_user_name_column"
down_revision = "0022_agent_project_model"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS name TEXT DEFAULT ''")


def downgrade() -> None:
    pass

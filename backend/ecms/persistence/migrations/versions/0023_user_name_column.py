"""Add name column to users table.

Revision ID: 0023
Revises: 0022
"""

from __future__ import annotations

from alembic import op
from ecms.persistence.migrations.compat import add_column_if_missing

revision = "0023_user_name_column"
down_revision = "0022_agent_project_model"
branch_labels = None
depends_on = None


def upgrade() -> None:
    add_column_if_missing("users", "name TEXT DEFAULT ''")


def downgrade() -> None:
    pass

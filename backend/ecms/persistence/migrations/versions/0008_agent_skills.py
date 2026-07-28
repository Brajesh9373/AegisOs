"""Ensure agent metadata columns and relax designation.

Revision ID: 0008
Revises: 0007
Create Date: 2026-07-11 00:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    if not _has_column("agents", "role_description"):
        op.add_column("agents", sa.Column("role_description", sa.Text(), nullable=True))
    if not _has_column("agents", "skills"):
        op.add_column("agents", sa.Column("skills", sa.JSON(), nullable=True))
    op.alter_column("agents", "designation", existing_type=sa.String(255), nullable=True, server_default="")


def downgrade() -> None:
    op.alter_column("agents", "designation", existing_type=sa.String(255), nullable=False, server_default=None)


def _has_column(table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))

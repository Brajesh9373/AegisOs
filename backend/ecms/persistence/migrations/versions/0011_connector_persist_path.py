"""Add clone_path to project_connectors table.

Revision ID: 0011
Revises: 0010
Create Date: 2026-07-11 00:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0011_connector_persist_path"
down_revision: str | None = "0010_drop_ctr_fks"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("project_connectors", sa.Column("persist_path", sa.String(1024), nullable=True))


def downgrade() -> None:
    op.drop_column("project_connectors", "persist_path")

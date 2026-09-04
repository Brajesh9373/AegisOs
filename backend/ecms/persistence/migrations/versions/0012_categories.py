"""Alembic migration: create categories table with seeded defaults.

Revision ID: 0012
Revises: 0011
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC

import sqlalchemy as sa
from alembic import op

from ecms.persistence.models.category import DEFAULT_CATEGORIES

revision: str = "0012_categories"
down_revision: str | None = "0011_connector_persist_path"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", sa.String(128), primary_key=True),
        sa.Column("name", sa.String(128), nullable=False, unique=True),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("color", sa.String(16), nullable=False),
        sa.Column("priority", sa.Integer, nullable=False),
        sa.Column("is_default", sa.Boolean, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
    # Seed defaults
    from datetime import datetime

    now = datetime.now(UTC)
    for c in DEFAULT_CATEGORIES:
        op.execute(
            sa.text(
                "INSERT INTO categories (id, name, description, color, priority, is_default, created_at, updated_at) "
                "VALUES (:id, :name, :description, :color, :priority, :is_default, :created_at, :updated_at)"
            ).bindparams(
                id=f"cat-{c['name']}",
                name=c["name"],
                description=c["description"],
                color=c["color"],
                priority=c["priority"],
                is_default=c["is_default"],
                created_at=now,
                updated_at=now,
            )
        )


def downgrade() -> None:
    op.drop_table("categories")

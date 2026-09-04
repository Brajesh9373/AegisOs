"""Add durable knowledge graph snapshot lifecycle metadata.

Revision ID: 0039
Revises: 0038
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0039_knowledge_graph_snapshots"
down_revision: str | None = "0038_normalize_governance_member_ids"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "knowledge_graph_snapshots",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("organization_id", sa.String(length=128), nullable=False),
        sa.Column("version", sa.String(length=64), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("state", sa.String(length=24), nullable=False),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("points_object_key", sa.String(length=1024), nullable=True),
        sa.Column("links_object_key", sa.String(length=1024), nullable=True),
        sa.Column("points_checksum", sa.String(length=64), nullable=True),
        sa.Column("links_checksum", sa.String(length=64), nullable=True),
        sa.Column("point_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("link_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("points_bytes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("links_bytes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("source_watermark", sa.String(length=255), nullable=True),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id", "version", name="uq_knowledge_graph_snapshot_org_version"
        ),
    )
    op.create_index(
        "ix_knowledge_graph_snapshots_organization_id",
        "knowledge_graph_snapshots",
        ["organization_id"],
    )
    op.create_index(
        "ix_knowledge_graph_snapshots_state",
        "knowledge_graph_snapshots",
        ["state"],
    )
    op.create_index(
        "ix_knowledge_graph_snapshot_org_created",
        "knowledge_graph_snapshots",
        ["organization_id", "created_at"],
    )
    op.create_index(
        "uq_knowledge_graph_snapshot_current_org",
        "knowledge_graph_snapshots",
        ["organization_id"],
        unique=True,
        postgresql_where=sa.text("is_current"),
    )


def downgrade() -> None:
    op.drop_table("knowledge_graph_snapshots")


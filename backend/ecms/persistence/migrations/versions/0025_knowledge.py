"""Knowledge base for BA agent augmentation.

Adds a `knowledge_entries` table that stores categorized knowledge (patterns,
anti-patterns, compliance rules, domain expertise, corrections) with embeddings
for semantic search. This powers the RAG-augmented BA agent.

Revision ID: 0025
Revises: 0024
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0025_knowledge"
down_revision: str | None = "0024_meetings"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.create_table(
        "knowledge_entries",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("category", sa.Text(), nullable=False, server_default=""),
        sa.Column("domain", sa.Text(), nullable=False, server_default=""),
        sa.Column("tags", sa.ARRAY(sa.Text()), server_default="{}"),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", sa.ARRAY(sa.Float()), nullable=True),
        sa.Column("source", sa.Text(), nullable=False, server_default="telegram"),
        sa.Column("contributor", sa.Text(), nullable=False, server_default=""),
        sa.Column("project_id", sa.Text(), nullable=True),
        sa.Column("chunk_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("parent_id", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index("idx_knowledge_category", "knowledge_entries", ["category"])
    op.create_index("idx_knowledge_domain", "knowledge_entries", ["domain"])
    op.create_index("idx_knowledge_source", "knowledge_entries", ["source"])
    op.create_index("idx_knowledge_project", "knowledge_entries", ["project_id"])
    op.create_index("idx_knowledge_tags", "knowledge_entries", ["tags"], postgresql_using="gin")
    op.execute(
        "CREATE INDEX idx_knowledge_content_fts ON knowledge_entries "
        "USING GIN(to_tsvector('english', content))"
    )


def downgrade() -> None:
    op.drop_table("knowledge_entries")

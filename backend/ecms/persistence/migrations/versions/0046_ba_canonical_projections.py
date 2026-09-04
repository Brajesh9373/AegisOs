"""Add independent tenant-bound canonical BA projections.

Revision ID: 0046
Revises: 0045
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0046_ba_canonical_projections"
down_revision: str | None = "0045_ba_stage_outcomes"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

_CLASSIFICATION = "classification IN ('public','internal','confidential','restricted')"
_LIFECYCLE = "lifecycle_state IN ('active','retracted')"


def upgrade() -> None:
    """Create canonical BA projections with queryable ACL and scope boundaries."""
    op.create_table(
        "ba_canonical_projections",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("organization_id", sa.String(128), nullable=False),
        sa.Column("project_id", sa.String(128), nullable=False),
        sa.Column("source_candidate_id", sa.String(64), nullable=False),
        sa.Column("canonical_key", sa.String(64), nullable=False),
        sa.Column("canonical_type", sa.String(128), nullable=False),
        sa.Column("projection_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("classification", sa.String(32), nullable=False),
        sa.Column("classification_rank", sa.Integer(), nullable=False),
        sa.Column("lifecycle_state", sa.String(24), nullable=False, server_default="active"),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("payload_checksum", sa.String(64), nullable=False),
        sa.Column("search_text", sa.Text(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("retracted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("id", "organization_id", name="uq_ba_canonical_projection_provenance"),
        sa.UniqueConstraint(
            "organization_id", "canonical_key", name="uq_ba_canonical_projection_org_key"
        ),
        sa.UniqueConstraint(
            "organization_id",
            "source_candidate_id",
            name="uq_ba_canonical_projection_source_candidate",
        ),
        sa.ForeignKeyConstraint(
            ["source_candidate_id", "organization_id"],
            ["ba_candidates.id", "ba_candidates.organization_id"],
            ondelete="RESTRICT",
            name="fk_ba_canonical_projection_candidate_provenance",
        ),
        sa.CheckConstraint(_CLASSIFICATION, name="ck_ba_canonical_projection_classification"),
        sa.CheckConstraint(
            "classification_rank BETWEEN 0 AND 3",
            name="ck_ba_canonical_projection_classification_rank",
        ),
        sa.CheckConstraint(_LIFECYCLE, name="ck_ba_canonical_projection_lifecycle"),
        sa.CheckConstraint(
            "projection_version > 0", name="ck_ba_canonical_projection_version"
        ),
    )
    op.create_index(
        "ix_ba_canonical_projection_access",
        "ba_canonical_projections",
        ["organization_id", "project_id", "lifecycle_state", "classification_rank", "created_at"],
    )
    op.create_index(
        "ix_ba_canonical_projection_org_project_type",
        "ba_canonical_projections",
        ["organization_id", "project_id", "canonical_type"],
    )

    op.create_table(
        "ba_canonical_projection_acls",
        sa.Column("projection_id", sa.String(64), nullable=False),
        sa.Column("organization_id", sa.String(128), nullable=False),
        sa.Column("actor_id", sa.String(128), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint(
            "projection_id",
            "organization_id",
            "actor_id",
            name="pk_ba_canonical_projection_acl",
        ),
        sa.ForeignKeyConstraint(
            ["projection_id", "organization_id"],
            ["ba_canonical_projections.id", "ba_canonical_projections.organization_id"],
            ondelete="CASCADE",
            name="fk_ba_canonical_projection_acl_provenance",
        ),
    )
    op.create_index(
        "ix_ba_canonical_projection_acl_lookup",
        "ba_canonical_projection_acls",
        ["organization_id", "actor_id", "projection_id"],
    )

    op.create_table(
        "ba_canonical_projection_scopes",
        sa.Column("projection_id", sa.String(64), nullable=False),
        sa.Column("organization_id", sa.String(128), nullable=False),
        sa.Column("scope_id", sa.String(128), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint(
            "projection_id",
            "organization_id",
            "scope_id",
            name="pk_ba_canonical_projection_scope",
        ),
        sa.ForeignKeyConstraint(
            ["projection_id", "organization_id"],
            ["ba_canonical_projections.id", "ba_canonical_projections.organization_id"],
            ondelete="CASCADE",
            name="fk_ba_canonical_projection_scope_provenance",
        ),
    )
    op.create_index(
        "ix_ba_canonical_projection_scope_lookup",
        "ba_canonical_projection_scopes",
        ["organization_id", "scope_id", "projection_id"],
    )


def downgrade() -> None:
    """Remove canonical BA projections and their tenant-bound access records."""
    op.drop_table("ba_canonical_projection_scopes")
    op.drop_table("ba_canonical_projection_acls")
    op.drop_table("ba_canonical_projections")

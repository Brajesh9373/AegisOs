"""Harden discovery provenance and add durable BA stage outcomes.

Revision ID: 0045
Revises: 0044
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0045_ba_stage_outcomes"
down_revision: str | None = "0044_project_human_assignments"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


_RECEIPT_STAGE = "stage IN ('understand','clarify','finalize','design_team')"
_CANDIDATE_STATE = (
    "state IN ('pending_approval','queued_for_projection','promoted','deduplicated','rejected')"
)
_OUTBOX_STATE = "state IN ('pending','leased','retry','completed','dead_letter','cancelled')"


def upgrade() -> None:
    """Add discovery tenancy columns and BA receipt/candidate/outbox tables."""
    # The legacy discovery table predates organization ownership. Columns remain
    # nullable during migration because standalone historical sessions cannot be
    # attributed safely. New application writes must stamp both fields.
    op.add_column("discovery_sessions", sa.Column("owner_id", sa.String(128), nullable=True))
    op.add_column("discovery_sessions", sa.Column("organization_id", sa.String(128), nullable=True))
    # Use correlated subqueries instead of ``UPDATE .. FROM`` so the backfill
    # works on both supported PostgreSQL and SQLite migration paths. The legacy
    # DDL declared ``ownerId`` without quoting it, so PostgreSQL stores the name
    # as ``ownerid``; SQLite resolves the same lowercase spelling case-insensitively.
    op.execute(
        "UPDATE discovery_sessions "
        "SET owner_id = COALESCE(owner_id, ("
        "SELECT projects.ownerid FROM business_projects AS projects "
        "WHERE projects.id = discovery_sessions.project_id"
        ")), organization_id = COALESCE(organization_id, ("
        "SELECT projects.organization_id FROM business_projects AS projects "
        "WHERE projects.id = discovery_sessions.project_id"
        ")) "
        "WHERE project_id IS NOT NULL "
        "AND (owner_id IS NULL OR organization_id IS NULL)"
    )
    op.create_index("ix_discovery_sessions_owner_id", "discovery_sessions", ["owner_id"])
    op.create_index(
        "ix_discovery_sessions_org_owner", "discovery_sessions", ["organization_id", "owner_id"]
    )

    op.create_table(
        "ba_stage_receipts",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("organization_id", sa.String(128), nullable=False),
        sa.Column("project_id", sa.String(128), nullable=True),
        sa.Column("discovery_session_id", sa.String(128), nullable=False),
        sa.Column("actor_id", sa.String(128), nullable=False),
        sa.Column("correlation_id", sa.String(128), nullable=False),
        sa.Column("stage", sa.String(32), nullable=False),
        sa.Column("idempotency_key", sa.String(64), nullable=False),
        sa.Column("context_snapshot_hash", sa.String(64), nullable=False),
        sa.Column("scope_partition_hash", sa.String(64), nullable=False),
        sa.Column("source_revision", sa.String(255), nullable=False),
        sa.Column("conversation_revision", sa.String(255), nullable=False),
        sa.Column("policy_revision", sa.String(255), nullable=False),
        sa.Column("profile_hash", sa.String(255), nullable=False),
        sa.Column("template_hash", sa.String(255), nullable=False),
        sa.Column("schema_hash", sa.String(255), nullable=False),
        sa.Column("classification_ceiling", sa.String(128), nullable=False),
        sa.Column("retention_policy", sa.String(128), nullable=False),
        sa.Column("source_checksum", sa.String(64), nullable=False),
        sa.Column("conversation_checksum", sa.String(64), nullable=False),
        sa.Column("evidence_checksum", sa.String(64), nullable=False),
        sa.Column("graph_checksum", sa.String(64), nullable=False),
        sa.Column("provenance_json", sa.JSON(), nullable=False),
        sa.Column("validated_output", sa.JSON(), nullable=False),
        sa.Column("output_checksum", sa.String(64), nullable=False),
        sa.Column("runtime_metadata_hash", sa.String(64), nullable=False),
        sa.Column("runtime_metadata_keys", sa.JSON(), nullable=False),
        sa.Column("execution_duration_ms", sa.Integer(), nullable=False),
        sa.Column("validation_attempts", sa.Integer(), nullable=False),
        sa.Column("candidate_outcomes", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("organization_id", "idempotency_key", name="uq_ba_stage_receipt_org_idempotency"),
        sa.UniqueConstraint("id", "organization_id", name="uq_ba_stage_receipt_provenance"),
        sa.CheckConstraint(_RECEIPT_STAGE, name="ck_ba_stage_receipt_stage"),
        sa.CheckConstraint(
            "validation_attempts IN (1,2)", name="ck_ba_stage_receipt_validation_attempts"
        ),
        sa.CheckConstraint(
            "execution_duration_ms >= 0", name="ck_ba_stage_receipt_nonnegative_duration"
        ),
    )
    op.create_index(
        "ix_ba_stage_receipts_organization_id", "ba_stage_receipts", ["organization_id"]
    )
    op.create_index("ix_ba_stage_receipts_project_id", "ba_stage_receipts", ["project_id"])
    op.create_index(
        "ix_ba_stage_receipts_discovery_session_id", "ba_stage_receipts", ["discovery_session_id"]
    )
    op.create_index(
        "ix_ba_stage_receipt_org_session_created",
        "ba_stage_receipts",
        ["organization_id", "discovery_session_id", "created_at"],
    )
    op.create_index(
        "ix_ba_stage_receipt_org_project_stage",
        "ba_stage_receipts",
        ["organization_id", "project_id", "stage"],
    )

    op.create_table(
        "ba_candidates",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("receipt_id", sa.String(64), nullable=False),
        sa.Column("organization_id", sa.String(128), nullable=False),
        sa.Column("project_id", sa.String(128), nullable=True),
        sa.Column("discovery_session_id", sa.String(128), nullable=False),
        sa.Column("kind", sa.String(64), nullable=False),
        sa.Column("candidate_key", sa.String(64), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("payload_checksum", sa.String(64), nullable=False),
        sa.Column("state", sa.String(32), nullable=False),
        sa.Column("approval_required", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("promoted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("organization_id", "candidate_key", name="uq_ba_candidate_org_idempotency"),
        sa.UniqueConstraint("id", "organization_id", name="uq_ba_candidate_provenance"),
        sa.ForeignKeyConstraint(
            ["receipt_id", "organization_id"],
            ["ba_stage_receipts.id", "ba_stage_receipts.organization_id"],
            ondelete="RESTRICT",
            name="fk_ba_candidate_receipt_provenance",
        ),
        sa.CheckConstraint(_CANDIDATE_STATE, name="ck_ba_candidate_state"),
        sa.CheckConstraint(
            "approval_required IN (TRUE,FALSE)", name="ck_ba_candidate_approval_required"
        ),
    )
    op.create_index("ix_ba_candidates_organization_id", "ba_candidates", ["organization_id"])
    op.create_index("ix_ba_candidates_project_id", "ba_candidates", ["project_id"])
    op.create_index(
        "ix_ba_candidates_discovery_session_id", "ba_candidates", ["discovery_session_id"]
    )
    op.create_index("ix_ba_candidates_state", "ba_candidates", ["state"])
    op.create_index(
        "ix_ba_candidate_org_state_created",
        "ba_candidates",
        ["organization_id", "state", "created_at"],
    )
    op.create_index(
        "ix_ba_candidate_org_project_kind",
        "ba_candidates",
        ["organization_id", "project_id", "kind"],
    )

    op.create_table(
        "ba_promotion_outbox",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("organization_id", sa.String(128), nullable=False),
        sa.Column("candidate_id", sa.String(64), nullable=False),
        sa.Column("event_type", sa.String(128), nullable=False),
        sa.Column("dedupe_key", sa.String(64), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("state", sa.String(32), nullable=False, server_default="pending"),
        sa.Column(
            "available_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("lease_owner", sa.String(255), nullable=True),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempt", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="12"),
        sa.Column("error_code", sa.String(128), nullable=True),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("organization_id", "dedupe_key", name="uq_ba_outbox_org_dedupe"),
        sa.ForeignKeyConstraint(
            ["candidate_id", "organization_id"],
            ["ba_candidates.id", "ba_candidates.organization_id"],
            ondelete="CASCADE",
            name="fk_ba_outbox_candidate_provenance",
        ),
        sa.CheckConstraint(_OUTBOX_STATE, name="ck_ba_outbox_state"),
        sa.CheckConstraint(
            "attempt >= 0 AND max_attempts > 0", name="ck_ba_outbox_attempt_bounds"
        ),
    )
    op.create_index("ix_ba_promotion_outbox_organization_id", "ba_promotion_outbox", ["organization_id"])
    op.create_index("ix_ba_promotion_outbox_state", "ba_promotion_outbox", ["state"])
    op.create_index(
        "ix_ba_outbox_claim",
        "ba_promotion_outbox",
        ["state", "available_at", "lease_expires_at"],
    )
    op.create_index(
        "ix_ba_outbox_org_state", "ba_promotion_outbox", ["organization_id", "state"]
    )


def downgrade() -> None:
    """Remove BA durability tables and discovery ownership indexes/columns."""
    op.drop_table("ba_promotion_outbox")
    op.drop_table("ba_candidates")
    op.drop_table("ba_stage_receipts")
    op.drop_index("ix_discovery_sessions_org_owner", table_name="discovery_sessions")
    op.drop_index("ix_discovery_sessions_owner_id", table_name="discovery_sessions")
    op.drop_column("discovery_sessions", "organization_id")
    op.drop_column("discovery_sessions", "owner_id")

"""Durable, organization-scoped Business Analyst stage outcomes.

The rows in this module are the canonical persistence boundary for accepted BA
stage output. They deliberately retain only bounded non-secret provenance and
validated artifacts; they never store prompts, bearer tokens, gateway values,
or raw authorization policy data.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from ecms.persistence.models.base import Base
from ecms.shared.time import utcnow

__all__ = ["BACandidate", "BAPromotionOutbox", "BAStageReceipt"]


class BAStageReceipt(Base):
    """Immutable record of one strictly validated BA stage result.

    ``discovery_session_id`` is intentionally an opaque provenance value rather
    than a foreign key until the legacy discovery table enforces organization
    ownership. Referencing it by bare ID today would weaken tenant isolation.
    """

    __tablename__ = "ba_stage_receipts"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "idempotency_key", name="uq_ba_stage_receipt_org_idempotency"
        ),
        UniqueConstraint("id", "organization_id", name="uq_ba_stage_receipt_provenance"),
        CheckConstraint(
            "stage IN ('understand','clarify','finalize','design_team')",
            name="ck_ba_stage_receipt_stage",
        ),
        CheckConstraint(
            "validation_attempts IN (1,2)",
            name="ck_ba_stage_receipt_validation_attempts",
        ),
        CheckConstraint(
            "execution_duration_ms >= 0", name="ck_ba_stage_receipt_nonnegative_duration"
        ),
        Index(
            "ix_ba_stage_receipt_org_session_created",
            "organization_id",
            "discovery_session_id",
            "created_at",
        ),
        Index("ix_ba_stage_receipt_org_project_stage", "organization_id", "project_id", "stage"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    project_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    discovery_session_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    actor_id: Mapped[str] = mapped_column(String(128), nullable=False)
    correlation_id: Mapped[str] = mapped_column(String(128), nullable=False)
    stage: Mapped[str] = mapped_column(String(32), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(64), nullable=False)
    context_snapshot_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    scope_partition_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    source_revision: Mapped[str] = mapped_column(String(255), nullable=False)
    conversation_revision: Mapped[str] = mapped_column(String(255), nullable=False)
    policy_revision: Mapped[str] = mapped_column(String(255), nullable=False)
    profile_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    template_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    schema_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    classification_ceiling: Mapped[str] = mapped_column(String(128), nullable=False)
    retention_policy: Mapped[str] = mapped_column(String(128), nullable=False)
    source_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    conversation_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    evidence_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    graph_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    provenance_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    validated_output: Mapped[Any] = mapped_column(JSON, nullable=False)
    output_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    runtime_metadata_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    runtime_metadata_keys: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    execution_duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    validation_attempts: Mapped[int] = mapped_column(Integer, nullable=False)
    candidate_outcomes: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, nullable=False, default=list
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )


class BACandidate(Base):
    """One policy-scoped, non-authoritative candidate derived from a receipt."""

    __tablename__ = "ba_candidates"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "candidate_key", name="uq_ba_candidate_org_idempotency"
        ),
        UniqueConstraint("id", "organization_id", name="uq_ba_candidate_provenance"),
        ForeignKeyConstraint(
            ["receipt_id", "organization_id"],
            ["ba_stage_receipts.id", "ba_stage_receipts.organization_id"],
            ondelete="RESTRICT",
            name="fk_ba_candidate_receipt_provenance",
        ),
        CheckConstraint(
            "state IN ('pending_approval','queued_for_projection','promoted','deduplicated','rejected')",
            name="ck_ba_candidate_state",
        ),
        CheckConstraint(
            "approval_required IN (TRUE,FALSE)", name="ck_ba_candidate_approval_required"
        ),
        Index("ix_ba_candidate_org_state_created", "organization_id", "state", "created_at"),
        Index("ix_ba_candidate_org_project_kind", "organization_id", "project_id", "kind"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    receipt_id: Mapped[str] = mapped_column(String(64), nullable=False)
    organization_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    project_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    discovery_session_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    candidate_key: Mapped[str] = mapped_column(String(64), nullable=False)
    payload_json: Mapped[Any] = mapped_column(JSON, nullable=False)
    payload_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    state: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    approval_required: Mapped[bool] = mapped_column(nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    promoted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class BAPromotionOutbox(Base):
    """Leaseable transactional outbox record for canonical candidate projection."""

    __tablename__ = "ba_promotion_outbox"
    __table_args__ = (
        UniqueConstraint("organization_id", "dedupe_key", name="uq_ba_outbox_org_dedupe"),
        ForeignKeyConstraint(
            ["candidate_id", "organization_id"],
            ["ba_candidates.id", "ba_candidates.organization_id"],
            ondelete="CASCADE",
            name="fk_ba_outbox_candidate_provenance",
        ),
        CheckConstraint(
            "state IN ('pending','leased','retry','completed','dead_letter','cancelled')",
            name="ck_ba_outbox_state",
        ),
        CheckConstraint(
            "attempt >= 0 AND max_attempts > 0",
            name="ck_ba_outbox_attempt_bounds",
        ),
        Index("ix_ba_outbox_claim", "state", "available_at", "lease_expires_at"),
        Index("ix_ba_outbox_org_state", "organization_id", "state"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    candidate_id: Mapped[str] = mapped_column(String(64), nullable=False)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    dedupe_key: Mapped[str] = mapped_column(String(64), nullable=False)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    state: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", index=True)
    available_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    lease_owner: Mapped[str | None] = mapped_column(String(255), nullable=True)
    lease_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    attempt: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=12)
    error_code: Mapped[str | None] = mapped_column(String(128), nullable=True)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

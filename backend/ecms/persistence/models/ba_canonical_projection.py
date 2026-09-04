"""Tenant-bound canonical projections derived from approved BA candidates.

This is an independent canonical store. It retains an explicitly classified,
lifecycle-controlled projection plus normalized actor ACL and scope records so
readers can enforce every security boundary inside their SQL query.
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
    PrimaryKeyConstraint,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from ecms.persistence.models.base import Base
from ecms.shared.time import utcnow

__all__ = [
    "BACanonicalProjection",
    "BACanonicalProjectionAcl",
    "BACanonicalProjectionScope",
]


class BACanonicalProjection(Base):
    """One active or retracted canonical artifact from a BA candidate.

    ``source_candidate_id`` remains tenant-bound through a composite foreign key.
    A project is mandatory: candidates without one are rejected before projection,
    rather than becoming globally discoverable enterprise facts.
    """

    __tablename__ = "ba_canonical_projections"
    __table_args__ = (
        UniqueConstraint("id", "organization_id", name="uq_ba_canonical_projection_provenance"),
        UniqueConstraint(
            "organization_id", "canonical_key", name="uq_ba_canonical_projection_org_key"
        ),
        UniqueConstraint(
            "organization_id",
            "source_candidate_id",
            name="uq_ba_canonical_projection_source_candidate",
        ),
        ForeignKeyConstraint(
            ["source_candidate_id", "organization_id"],
            ["ba_candidates.id", "ba_candidates.organization_id"],
            ondelete="RESTRICT",
            name="fk_ba_canonical_projection_candidate_provenance",
        ),
        CheckConstraint(
            "classification IN ('public','internal','confidential','restricted')",
            name="ck_ba_canonical_projection_classification",
        ),
        CheckConstraint(
            "classification_rank BETWEEN 0 AND 3",
            name="ck_ba_canonical_projection_classification_rank",
        ),
        CheckConstraint(
            "lifecycle_state IN ('active','retracted')",
            name="ck_ba_canonical_projection_lifecycle",
        ),
        CheckConstraint(
            "projection_version > 0", name="ck_ba_canonical_projection_version"
        ),
        Index(
            "ix_ba_canonical_projection_access",
            "organization_id",
            "project_id",
            "lifecycle_state",
            "classification_rank",
            "created_at",
        ),
        Index(
            "ix_ba_canonical_projection_org_project_type",
            "organization_id",
            "project_id",
            "canonical_type",
        ),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    project_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    source_candidate_id: Mapped[str] = mapped_column(String(64), nullable=False)
    canonical_key: Mapped[str] = mapped_column(String(64), nullable=False)
    canonical_type: Mapped[str] = mapped_column(String(128), nullable=False)
    projection_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    classification: Mapped[str] = mapped_column(String(32), nullable=False)
    classification_rank: Mapped[int] = mapped_column(Integer, nullable=False)
    lifecycle_state: Mapped[str] = mapped_column(String(24), nullable=False, default="active")
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    payload_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    search_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )
    retracted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class BACanonicalProjectionAcl(Base):
    """Explicit actor allow-list for one canonical projection.

    No wildcard principal is supported. Sharing is an intentional future operation
    that inserts a separately auditable row instead of broadening a query default.
    """

    __tablename__ = "ba_canonical_projection_acls"
    __table_args__ = (
        PrimaryKeyConstraint(
            "projection_id",
            "organization_id",
            "actor_id",
            name="pk_ba_canonical_projection_acl",
        ),
        ForeignKeyConstraint(
            ["projection_id", "organization_id"],
            ["ba_canonical_projections.id", "ba_canonical_projections.organization_id"],
            ondelete="CASCADE",
            name="fk_ba_canonical_projection_acl_provenance",
        ),
        Index(
            "ix_ba_canonical_projection_acl_lookup",
            "organization_id",
            "actor_id",
            "projection_id",
        ),
    )

    projection_id: Mapped[str] = mapped_column(String(64), nullable=False)
    organization_id: Mapped[str] = mapped_column(String(128), nullable=False)
    actor_id: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )


class BACanonicalProjectionScope(Base):
    """Explicit project/workspace scope allow-list for a canonical projection."""

    __tablename__ = "ba_canonical_projection_scopes"
    __table_args__ = (
        PrimaryKeyConstraint(
            "projection_id",
            "organization_id",
            "scope_id",
            name="pk_ba_canonical_projection_scope",
        ),
        ForeignKeyConstraint(
            ["projection_id", "organization_id"],
            ["ba_canonical_projections.id", "ba_canonical_projections.organization_id"],
            ondelete="CASCADE",
            name="fk_ba_canonical_projection_scope_provenance",
        ),
        Index(
            "ix_ba_canonical_projection_scope_lookup",
            "organization_id",
            "scope_id",
            "projection_id",
        ),
    )

    projection_id: Mapped[str] = mapped_column(String(64), nullable=False)
    organization_id: Mapped[str] = mapped_column(String(128), nullable=False)
    scope_id: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )

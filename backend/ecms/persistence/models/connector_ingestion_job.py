"""Durable lifecycle record for asynchronous connector ingestion."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from ecms.persistence.models.base import Base
from ecms.shared.time import utcnow

__all__ = ["ConnectorIngestionJob"]


class ConnectorIngestionJob(Base):
    """One durable, tenant-scoped connector ingestion attempt."""

    __tablename__ = "connector_ingestion_jobs"
    __table_args__ = (
        Index(
            "uq_connector_ingestion_active_source",
            "organization_id",
            "repository_identity",
            "branch",
            unique=True,
            postgresql_where=text(
                "state IN ('queued','validating','cloning','scanning','extracting',"
                "'writing','snapshotting','cancel_requested','retrying')"
            ),
            sqlite_where=text(
                "state IN ('queued','validating','cloning','scanning','extracting',"
                "'writing','snapshotting','cancel_requested','retrying')"
            ),
        ),
        Index(
            "ix_connector_ingestion_org_created",
            "organization_id",
            "created_at",
        ),
        UniqueConstraint(
            "organization_id",
            "idempotency_key",
            name="uq_connector_ingestion_org_idempotency",
        ),
        UniqueConstraint(
            "id",
            "organization_id",
            name="uq_connector_ingestion_job_provenance",
        ),
        CheckConstraint(
            "state IN ('queued','validating','cloning','scanning','extracting',"
            "'writing','snapshotting','cancel_requested','retrying','ready','failed',"
            "'cancelled')",
            name="ck_connector_ingestion_job_state",
        ),
        CheckConstraint(
            "progress_percent >= 0 AND progress_percent <= 100 "
            "AND files_discovered >= 0 AND files_processed >= 0 "
            "AND nodes_written >= 0 AND edges_written >= 0 AND attempt >= 0",
            name="ck_connector_ingestion_job_nonnegative",
        ),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    workspace_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    connection_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    repository_identity: Mapped[str] = mapped_column(String(1024), nullable=False)
    repository_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    branch: Mapped[str] = mapped_column(String(255), nullable=False, default="main")
    requested_revision: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resolved_revision: Mapped[str | None] = mapped_column(String(255), nullable=True)
    state: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    stage: Mapped[str] = mapped_column(String(32), nullable=False)
    progress_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    files_discovered: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    files_processed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    nodes_written: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    edges_written: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    lease_owner: Mapped[str | None] = mapped_column(String(255), nullable=True)
    lease_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    attempt: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    checkpoint: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    error_code: Mapped[str | None] = mapped_column(String(128), nullable=True)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancellation_requested: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    idempotency_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

"""Durable partitioning records for parallel connector ingestion."""

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

__all__ = [
    "ConnectorIngestionManifest",
    "ConnectorIngestionPartition",
    "ConnectorIngestionStageBatch",
]


class ConnectorIngestionManifest(Base):
    """Immutable description of the files resolved for one ingestion job."""

    __tablename__ = "connector_ingestion_manifests"
    __table_args__ = (
        UniqueConstraint("job_id", name="uq_connector_ingestion_manifest_job"),
        UniqueConstraint(
            "id", "job_id", "organization_id", name="uq_connector_ingestion_manifest_provenance"
        ),
        ForeignKeyConstraint(
            ["job_id", "organization_id"],
            ["connector_ingestion_jobs.id", "connector_ingestion_jobs.organization_id"],
            ondelete="CASCADE",
            name="fk_connector_ingestion_manifest_job_provenance",
        ),
        CheckConstraint(
            "state IN ('building','ready','failed','cancelled')",
            name="ck_connector_ingestion_manifest_state",
        ),
        CheckConstraint(
            "file_count >= 0 AND total_weight >= 0 AND partition_count >= 0",
            name="ck_connector_ingestion_manifest_nonnegative",
        ),
        Index("ix_connector_ingestion_manifest_org_created", "organization_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    job_id: Mapped[str] = mapped_column(String(64), nullable=False)
    organization_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    resolved_revision: Mapped[str] = mapped_column(String(255), nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    object_key: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    state: Mapped[str] = mapped_column(String(24), nullable=False, default="building", index=True)
    file_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_weight: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    partition_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ConnectorIngestionPartition(Base):
    """A deterministic, exclusively leased slice of an immutable manifest."""

    __tablename__ = "connector_ingestion_partitions"
    __table_args__ = (
        UniqueConstraint(
            "manifest_id", "partition_number", name="uq_connector_ingestion_partition_number"
        ),
        UniqueConstraint(
            "id", "job_id", "organization_id", name="uq_connector_ingestion_partition_provenance"
        ),
        ForeignKeyConstraint(
            ["manifest_id", "job_id", "organization_id"],
            [
                "connector_ingestion_manifests.id",
                "connector_ingestion_manifests.job_id",
                "connector_ingestion_manifests.organization_id",
            ],
            ondelete="CASCADE",
            name="fk_connector_ingestion_partition_manifest_provenance",
        ),
        CheckConstraint(
            "state IN ('pending','claimed','extracting','staged','retry','committed',"
            "'failed','cancelled','superseded')",
            name="ck_connector_ingestion_partition_state",
        ),
        CheckConstraint(
            "partition_number >= 0 AND file_count >= 0 AND estimated_weight >= 0 "
            "AND files_processed >= 0 AND nodes_extracted >= 0 "
            "AND edges_extracted >= 0 AND attempt >= 0",
            name="ck_connector_ingestion_partition_nonnegative",
        ),
        Index("ix_connector_ingestion_partition_claim", "state", "lease_expires_at"),
        Index("ix_connector_ingestion_partition_job_state", "job_id", "state"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    manifest_id: Mapped[str] = mapped_column(String(64), nullable=False)
    job_id: Mapped[str] = mapped_column(String(64), nullable=False)
    organization_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    partition_number: Mapped[int] = mapped_column(Integer, nullable=False)
    state: Mapped[str] = mapped_column(String(24), nullable=False, default="pending", index=True)
    file_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    estimated_weight: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    files_processed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    nodes_extracted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    edges_extracted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    lease_owner: Mapped[str | None] = mapped_column(String(255), nullable=True)
    lease_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    attempt: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    checkpoint: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ConnectorIngestionStageBatch(Base):
    """An immutable, checksummed graph batch produced by one partition."""

    __tablename__ = "connector_ingestion_stage_batches"
    __table_args__ = (
        UniqueConstraint(
            "partition_id", "sequence_number", name="uq_connector_ingestion_stage_sequence"
        ),
        UniqueConstraint("partition_id", "checksum", name="uq_connector_ingestion_stage_checksum"),
        ForeignKeyConstraint(
            ["partition_id", "job_id", "organization_id"],
            [
                "connector_ingestion_partitions.id",
                "connector_ingestion_partitions.job_id",
                "connector_ingestion_partitions.organization_id",
            ],
            ondelete="CASCADE",
            name="fk_connector_ingestion_stage_partition_provenance",
        ),
        CheckConstraint(
            "state IN ('staged','writing','committed','failed','cancelled')",
            name="ck_connector_ingestion_stage_state",
        ),
        CheckConstraint(
            "sequence_number >= 0 AND node_count >= 0 AND edge_count >= 0 "
            "AND byte_count >= 0 AND attempt >= 0",
            name="ck_connector_ingestion_stage_nonnegative",
        ),
        Index("ix_connector_ingestion_stage_job_state", "job_id", "state"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    partition_id: Mapped[str] = mapped_column(String(64), nullable=False)
    job_id: Mapped[str] = mapped_column(String(64), nullable=False)
    organization_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    object_key: Mapped[str] = mapped_column(String(1024), nullable=False)
    state: Mapped[str] = mapped_column(String(24), nullable=False, default="staged", index=True)
    node_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    edge_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    byte_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    writer_owner: Mapped[str | None] = mapped_column(String(255), nullable=True)
    writer_lease_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    attempt: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    committed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

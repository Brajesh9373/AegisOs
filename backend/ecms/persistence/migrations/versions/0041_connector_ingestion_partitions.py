"""Add durable manifests, partitions, and staged graph batches.

Revision ID: 0041
Revises: 0040
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0041"
down_revision: str | None = "0040"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    """Create the durable fan-out/fan-in persistence domain."""
    op.create_table(
        "connector_ingestion_manifests",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column(
            "job_id",
            sa.String(64),
            sa.ForeignKey("connector_ingestion_jobs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("organization_id", sa.String(128), nullable=False),
        sa.Column("resolved_revision", sa.String(255), nullable=False),
        sa.Column("checksum", sa.String(64), nullable=False),
        sa.Column("object_key", sa.String(1024), nullable=True),
        sa.Column("state", sa.String(24), nullable=False, server_default="building"),
        sa.Column("file_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_weight", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("partition_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("job_id", name="uq_connector_ingestion_manifest_job"),
        sa.UniqueConstraint(
            "organization_id",
            "resolved_revision",
            "checksum",
            name="uq_connector_ingestion_manifest_revision_checksum",
        ),
    )
    op.create_index(
        "ix_connector_ingestion_manifests_organization_id",
        "connector_ingestion_manifests",
        ["organization_id"],
    )
    op.create_index(
        "ix_connector_ingestion_manifests_state",
        "connector_ingestion_manifests",
        ["state"],
    )
    op.create_index(
        "ix_connector_ingestion_manifest_org_created",
        "connector_ingestion_manifests",
        ["organization_id", "created_at"],
    )

    op.create_table(
        "connector_ingestion_partitions",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column(
            "manifest_id",
            sa.String(64),
            sa.ForeignKey("connector_ingestion_manifests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "job_id",
            sa.String(64),
            sa.ForeignKey("connector_ingestion_jobs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("organization_id", sa.String(128), nullable=False),
        sa.Column("partition_number", sa.Integer(), nullable=False),
        sa.Column("state", sa.String(24), nullable=False, server_default="pending"),
        sa.Column("file_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("estimated_weight", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("files_processed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("nodes_extracted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("edges_extracted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("lease_owner", sa.String(255), nullable=True),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempt", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("checkpoint", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "manifest_id", "partition_number", name="uq_connector_ingestion_partition_number"
        ),
    )
    op.create_index(
        "ix_connector_ingestion_partitions_organization_id",
        "connector_ingestion_partitions",
        ["organization_id"],
    )
    op.create_index(
        "ix_connector_ingestion_partitions_state",
        "connector_ingestion_partitions",
        ["state"],
    )
    op.create_index(
        "ix_connector_ingestion_partition_claim",
        "connector_ingestion_partitions",
        ["state", "lease_expires_at"],
    )
    op.create_index(
        "ix_connector_ingestion_partition_job_state",
        "connector_ingestion_partitions",
        ["job_id", "state"],
    )

    op.create_table(
        "connector_ingestion_stage_batches",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column(
            "partition_id",
            sa.String(64),
            sa.ForeignKey("connector_ingestion_partitions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "job_id",
            sa.String(64),
            sa.ForeignKey("connector_ingestion_jobs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("organization_id", sa.String(128), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("checksum", sa.String(64), nullable=False),
        sa.Column("object_key", sa.String(1024), nullable=False),
        sa.Column("state", sa.String(24), nullable=False, server_default="staged"),
        sa.Column("node_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("edge_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("byte_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("writer_owner", sa.String(255), nullable=True),
        sa.Column("writer_lease_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempt", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("committed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "partition_id", "sequence_number", name="uq_connector_ingestion_stage_sequence"
        ),
        sa.UniqueConstraint(
            "partition_id", "checksum", name="uq_connector_ingestion_stage_checksum"
        ),
    )
    op.create_index(
        "ix_connector_ingestion_stage_batches_organization_id",
        "connector_ingestion_stage_batches",
        ["organization_id"],
    )
    op.create_index(
        "ix_connector_ingestion_stage_batches_state",
        "connector_ingestion_stage_batches",
        ["state"],
    )
    op.create_index(
        "ix_connector_ingestion_stage_job_state",
        "connector_ingestion_stage_batches",
        ["job_id", "state"],
    )


def downgrade() -> None:
    """Remove the partitioning persistence domain."""
    op.drop_table("connector_ingestion_stage_batches")
    op.drop_table("connector_ingestion_partitions")
    op.drop_table("connector_ingestion_manifests")

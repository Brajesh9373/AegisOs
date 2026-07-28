"""Harden connector ingestion tree integrity and lifecycle constraints.

Revision ID: 0042
Revises: 0041
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0042"
down_revision: str | None = "0041"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    """Enforce provenance, repeatable revisions, legal states, and counters."""
    op.create_unique_constraint(
        "uq_connector_ingestion_job_provenance",
        "connector_ingestion_jobs",
        ["id", "organization_id"],
    )
    op.drop_constraint(
        "uq_connector_ingestion_manifest_revision_checksum",
        "connector_ingestion_manifests",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_connector_ingestion_manifest_provenance",
        "connector_ingestion_manifests",
        ["id", "job_id", "organization_id"],
    )
    op.create_unique_constraint(
        "uq_connector_ingestion_partition_provenance",
        "connector_ingestion_partitions",
        ["id", "job_id", "organization_id"],
    )
    op.create_foreign_key(
        "fk_connector_ingestion_manifest_job_provenance",
        "connector_ingestion_manifests",
        "connector_ingestion_jobs",
        ["job_id", "organization_id"],
        ["id", "organization_id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_connector_ingestion_partition_manifest_provenance",
        "connector_ingestion_partitions",
        "connector_ingestion_manifests",
        ["manifest_id", "job_id", "organization_id"],
        ["id", "job_id", "organization_id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_connector_ingestion_stage_partition_provenance",
        "connector_ingestion_stage_batches",
        "connector_ingestion_partitions",
        ["partition_id", "job_id", "organization_id"],
        ["id", "job_id", "organization_id"],
        ondelete="CASCADE",
    )
    op.create_check_constraint(
        "ck_connector_ingestion_job_state",
        "connector_ingestion_jobs",
        "state IN ('queued','validating','cloning','scanning','extracting',"
        "'writing','snapshotting','cancel_requested','retrying','ready','failed',"
        "'cancelled')",
    )
    op.create_check_constraint(
        "ck_connector_ingestion_job_nonnegative",
        "connector_ingestion_jobs",
        "progress_percent >= 0 AND progress_percent <= 100 "
        "AND files_discovered >= 0 AND files_processed >= 0 "
        "AND nodes_written >= 0 AND edges_written >= 0 AND attempt >= 0",
    )
    op.create_check_constraint(
        "ck_connector_ingestion_manifest_state",
        "connector_ingestion_manifests",
        "state IN ('building','ready','failed','cancelled')",
    )
    op.create_check_constraint(
        "ck_connector_ingestion_manifest_nonnegative",
        "connector_ingestion_manifests",
        "file_count >= 0 AND total_weight >= 0 AND partition_count >= 0",
    )
    op.create_check_constraint(
        "ck_connector_ingestion_partition_state",
        "connector_ingestion_partitions",
        "state IN ('pending','claimed','extracting','staged','retry','committed',"
        "'failed','cancelled','superseded')",
    )
    op.create_check_constraint(
        "ck_connector_ingestion_partition_nonnegative",
        "connector_ingestion_partitions",
        "partition_number >= 0 AND file_count >= 0 AND estimated_weight >= 0 "
        "AND files_processed >= 0 AND nodes_extracted >= 0 "
        "AND edges_extracted >= 0 AND attempt >= 0",
    )
    op.create_check_constraint(
        "ck_connector_ingestion_stage_state",
        "connector_ingestion_stage_batches",
        "state IN ('staged','writing','committed','failed','cancelled')",
    )
    op.create_check_constraint(
        "ck_connector_ingestion_stage_nonnegative",
        "connector_ingestion_stage_batches",
        "sequence_number >= 0 AND node_count >= 0 AND edge_count >= 0 "
        "AND byte_count >= 0 AND attempt >= 0",
    )


def downgrade() -> None:
    """Restore the original 0041 constraint set."""
    op.drop_constraint(
        "ck_connector_ingestion_stage_nonnegative",
        "connector_ingestion_stage_batches",
        type_="check",
    )
    op.drop_constraint(
        "ck_connector_ingestion_stage_state",
        "connector_ingestion_stage_batches",
        type_="check",
    )
    op.drop_constraint(
        "ck_connector_ingestion_partition_nonnegative",
        "connector_ingestion_partitions",
        type_="check",
    )
    op.drop_constraint(
        "ck_connector_ingestion_partition_state",
        "connector_ingestion_partitions",
        type_="check",
    )
    op.drop_constraint(
        "ck_connector_ingestion_manifest_nonnegative",
        "connector_ingestion_manifests",
        type_="check",
    )
    op.drop_constraint(
        "ck_connector_ingestion_manifest_state",
        "connector_ingestion_manifests",
        type_="check",
    )
    op.drop_constraint(
        "ck_connector_ingestion_job_nonnegative",
        "connector_ingestion_jobs",
        type_="check",
    )
    op.drop_constraint(
        "ck_connector_ingestion_job_state",
        "connector_ingestion_jobs",
        type_="check",
    )
    op.drop_constraint(
        "fk_connector_ingestion_stage_partition_provenance",
        "connector_ingestion_stage_batches",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_connector_ingestion_partition_manifest_provenance",
        "connector_ingestion_partitions",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_connector_ingestion_manifest_job_provenance",
        "connector_ingestion_manifests",
        type_="foreignkey",
    )
    op.drop_constraint(
        "uq_connector_ingestion_partition_provenance",
        "connector_ingestion_partitions",
        type_="unique",
    )
    op.drop_constraint(
        "uq_connector_ingestion_manifest_provenance",
        "connector_ingestion_manifests",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_connector_ingestion_manifest_revision_checksum",
        "connector_ingestion_manifests",
        ["organization_id", "resolved_revision", "checksum"],
    )
    op.drop_constraint(
        "uq_connector_ingestion_job_provenance",
        "connector_ingestion_jobs",
        type_="unique",
    )

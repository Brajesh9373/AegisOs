"""Add durable asynchronous connector ingestion state.

Revision ID: 0040
Revises: 0039
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0040"
down_revision: str | None = "0039"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

_ACTIVE = (
    "state IN ('queued','validating','cloning','scanning','extracting',"
    "'writing','snapshotting','cancel_requested','retrying')"
)


def upgrade() -> None:
    """Create jobs and extend connection synchronization metadata."""
    op.add_column("connections", sa.Column("organization_id", sa.String(128), nullable=True))
    op.add_column("connections", sa.Column("sync_state", sa.String(32), nullable=True))
    op.add_column(
        "connections", sa.Column("current_ingestion_job_id", sa.String(64), nullable=True)
    )
    op.add_column(
        "connections", sa.Column("last_successful_revision", sa.String(255), nullable=True)
    )
    op.add_column(
        "connections", sa.Column("last_successful_snapshot_version", sa.String(64), nullable=True)
    )
    op.add_column("connections", sa.Column("last_error_summary", sa.Text(), nullable=True))
    op.create_index("ix_connections_organization_id", "connections", ["organization_id"])

    op.create_table(
        "connector_ingestion_jobs",
        sa.Column("id", sa.String(64), nullable=False),
        sa.Column("organization_id", sa.String(128), nullable=False),
        sa.Column("workspace_id", sa.String(128), nullable=True),
        sa.Column("connection_id", sa.Integer(), nullable=False),
        sa.Column("repository_identity", sa.String(1024), nullable=False),
        sa.Column("repository_url", sa.String(2048), nullable=False),
        sa.Column("branch", sa.String(255), nullable=False, server_default="main"),
        sa.Column("requested_revision", sa.String(255), nullable=True),
        sa.Column("resolved_revision", sa.String(255), nullable=True),
        sa.Column("state", sa.String(32), nullable=False),
        sa.Column("stage", sa.String(32), nullable=False),
        sa.Column("progress_percent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("files_discovered", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("files_processed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("nodes_written", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("edges_written", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("lease_owner", sa.String(255), nullable=True),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempt", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("checkpoint", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("error_code", sa.String(128), nullable=True),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.Column(
            "cancellation_requested", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("idempotency_key", sa.String(255), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id",
            "idempotency_key",
            name="uq_connector_ingestion_org_idempotency",
        ),
    )
    op.create_index(
        "ix_connector_ingestion_jobs_organization_id",
        "connector_ingestion_jobs",
        ["organization_id"],
    )
    op.create_index(
        "ix_connector_ingestion_jobs_workspace_id", "connector_ingestion_jobs", ["workspace_id"]
    )
    op.create_index(
        "ix_connector_ingestion_jobs_connection_id", "connector_ingestion_jobs", ["connection_id"]
    )
    op.create_index("ix_connector_ingestion_jobs_state", "connector_ingestion_jobs", ["state"])
    op.create_index(
        "ix_connector_ingestion_org_created",
        "connector_ingestion_jobs",
        ["organization_id", "created_at"],
    )
    op.create_index(
        "uq_connector_ingestion_active_source",
        "connector_ingestion_jobs",
        ["organization_id", "repository_identity", "branch"],
        unique=True,
        postgresql_where=sa.text(_ACTIVE),
    )


def downgrade() -> None:
    """Remove jobs and connection synchronization metadata."""
    op.drop_table("connector_ingestion_jobs")
    op.drop_index("ix_connections_organization_id", table_name="connections")
    op.drop_column("connections", "last_error_summary")
    op.drop_column("connections", "last_successful_snapshot_version")
    op.drop_column("connections", "last_successful_revision")
    op.drop_column("connections", "current_ingestion_job_id")
    op.drop_column("connections", "sync_state")
    op.drop_column("connections", "organization_id")

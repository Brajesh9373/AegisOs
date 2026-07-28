"""Connector ingestion state machine and submission semantics."""

from __future__ import annotations

import re
from datetime import datetime
from urllib.parse import urlsplit, urlunsplit
from uuid import uuid4

from ecms.persistence.models.connector_ingestion_job import ConnectorIngestionJob
from ecms.persistence.repositories.connector_ingestion_job import (
    ConnectorIngestionJobRepository,
)
from ecms.shared.time import utcnow

TERMINAL_STATES = frozenset({"ready", "failed", "cancelled"})
LEGAL_TRANSITIONS = {
    "queued": {"validating", "cancel_requested", "failed"},
    "validating": {"cloning", "cancel_requested", "failed"},
    "cloning": {"scanning", "cancel_requested", "failed"},
    "scanning": {"extracting", "cancel_requested", "failed"},
    "extracting": {"writing", "cancel_requested", "failed"},
    "writing": {"snapshotting", "cancel_requested", "failed"},
    "snapshotting": {"ready", "cancel_requested", "failed"},
    "cancel_requested": {"cancelled", "failed"},
    "retrying": {"queued", "cancel_requested", "failed"},
    "ready": set(),
    "failed": {"retrying"},
    "cancelled": {"retrying"},
}
_BRANCH_PATTERN = re.compile(r"^[A-Za-z0-9._/-]{1,255}$")

__all__ = [
    "LEGAL_TRANSITIONS",
    "TERMINAL_STATES",
    "ConnectorIngestionService",
    "normalize_repository_identity",
]


def normalize_repository_identity(repository_url: str) -> str:
    """Produce a credential-free stable repository identity."""
    value = repository_url.strip()
    if re.match(r"^[^/@:\s]+@[^/:\s]+:.+$", value):
        user_host, path = value.split(":", 1)
        host = user_host.rsplit("@", 1)[-1].lower()
        normalized_path = path.strip("/").removesuffix(".git")
        if not normalized_path:
            raise ValueError("repository URL has no path")
        return f"ssh://{host}/{normalized_path}"
    parsed = urlsplit(value)
    if parsed.scheme.lower() not in {"http", "https", "ssh", "git"} or not parsed.hostname:
        raise ValueError("repository URL must use http, https, ssh, git, or SCP syntax")
    if parsed.username or parsed.password:
        raise ValueError("repository URL must not contain credentials")
    path = parsed.path.rstrip("/").removesuffix(".git")
    if not path or path == "/":
        raise ValueError("repository URL has no repository path")
    port = f":{parsed.port}" if parsed.port else ""
    return urlunsplit((parsed.scheme.lower(), f"{parsed.hostname.lower()}{port}", path, "", ""))


class ConnectorIngestionService:
    """Enforce submission idempotency and legal lifecycle transitions."""

    def __init__(self, repository: ConnectorIngestionJobRepository) -> None:
        """Bind the domain service to a transactional repository."""
        self._repository = repository

    async def submit(
        self,
        *,
        organization_id: str,
        workspace_id: str | None,
        connection_id: int,
        repository_url: str,
        branch: str,
        requested_revision: str | None,
        idempotency_key: str | None,
    ) -> tuple[ConnectorIngestionJob, bool]:
        """Create a queued job or return an equivalent durable request."""
        normalized_branch = branch.strip() or "main"
        if not _BRANCH_PATTERN.fullmatch(normalized_branch) or ".." in normalized_branch:
            raise ValueError("invalid Git branch")
        identity = normalize_repository_identity(repository_url)
        if idempotency_key:
            existing = await self._repository.get_by_idempotency_key(
                organization_id, idempotency_key
            )
            if existing:
                return existing, False
        existing = await self._repository.get_active(organization_id, identity, normalized_branch)
        if existing:
            return existing, False
        job = ConnectorIngestionJob(
            id=str(uuid4()),
            organization_id=organization_id,
            workspace_id=workspace_id,
            connection_id=connection_id,
            repository_identity=identity,
            repository_url=repository_url,
            branch=normalized_branch,
            requested_revision=requested_revision,
            state="queued",
            stage="queued",
            idempotency_key=idempotency_key,
        )
        await self._repository.add(job)
        await self._repository.mark_connection_job(
            connection_id,
            organization_id=organization_id,
            job_id=job.id,
            sync_state=job.state,
        )
        return job, True

    async def transition(
        self,
        job: ConnectorIngestionJob,
        target: str,
        *,
        now: datetime | None = None,
        error_code: str | None = None,
        error_summary: str | None = None,
    ) -> ConnectorIngestionJob:
        """Apply one legal state transition and its terminal invariants."""
        if target not in LEGAL_TRANSITIONS.get(job.state, set()):
            raise ValueError(f"illegal ingestion transition: {job.state} -> {target}")
        timestamp = now or utcnow()
        job.state = target
        job.stage = target
        job.updated_at = timestamp
        if target not in TERMINAL_STATES:
            job.completed_at = None
        if target in TERMINAL_STATES:
            job.completed_at = timestamp
            job.lease_owner = None
            job.lease_expires_at = None
            job.progress_percent = 100 if target == "ready" else job.progress_percent
        if target == "failed":
            job.error_code = error_code or "INGESTION_FAILED"
            job.error_summary = (error_summary or "Connector ingestion failed")[:4_000]
        elif target not in {"retrying"}:
            job.error_code = None
            job.error_summary = None
        if target == "cancel_requested":
            job.cancellation_requested = True
        await self._repository.mark_connection_job(
            job.connection_id,
            organization_id=job.organization_id,
            job_id=job.id,
            sync_state=target,
            error_summary=job.error_summary,
        )
        return job

    async def request_cancellation(self, job: ConnectorIngestionJob) -> ConnectorIngestionJob:
        """Mark an active job for cooperative cancellation idempotently."""
        if job.state == "cancel_requested":
            return job
        if job.state in TERMINAL_STATES:
            raise ValueError("terminal ingestion jobs cannot be cancelled")
        return await self.transition(job, "cancel_requested")

    async def retry(self, failed: ConnectorIngestionJob) -> ConnectorIngestionJob:
        """Create a fresh attempt while retaining the failed job history."""
        if failed.state not in {"failed", "cancelled"}:
            raise ValueError("only failed or cancelled ingestion jobs can be retried")
        existing = await self._repository.get_active(
            failed.organization_id,
            failed.repository_identity,
            failed.branch,
        )
        if existing:
            return existing
        retried = ConnectorIngestionJob(
            id=str(uuid4()),
            organization_id=failed.organization_id,
            workspace_id=failed.workspace_id,
            connection_id=failed.connection_id,
            repository_identity=failed.repository_identity,
            repository_url=failed.repository_url,
            branch=failed.branch,
            requested_revision=failed.requested_revision,
            state="queued",
            stage="queued",
            attempt=failed.attempt + 1,
        )
        await self._repository.add(retried)
        await self._repository.mark_connection_job(
            retried.connection_id,
            organization_id=retried.organization_id,
            job_id=retried.id,
            sync_state=retried.state,
        )
        return retried

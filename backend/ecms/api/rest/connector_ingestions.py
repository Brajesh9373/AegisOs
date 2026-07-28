"""Non-blocking API contract for durable connector ingestion."""

from __future__ import annotations

import json
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from redis.asyncio import Redis

from ecms.api.rest.knowledge_graph_snapshots import (
    _organization_id,
    require_graph_identity,
)
from ecms.auth import Identity
from ecms.configuration.schemas.settings import get_settings
from ecms.connectors.ingestion.queue import IngestionQueue
from ecms.connectors.ingestion.service import ConnectorIngestionService
from ecms.persistence.database.rest_session import db_session
from ecms.persistence.models.connector_ingestion_job import ConnectorIngestionJob
from ecms.persistence.repositories.connector_ingestion_job import (
    ConnectorIngestionJobRepository,
)
from ecms.persistence.repositories.connector_ingestion_partition import (
    ConnectorIngestionPartitionRepository,
    ConnectorIngestionStageBatchRepository,
)

router = APIRouter(prefix="/api/connector-ingestions", tags=["connector-ingestions"])


class SubmitIngestion(BaseModel):
    """Request a sync for an existing authenticated connection."""

    connection_id: int = Field(gt=0)
    workspace_id: str | None = Field(default=None, max_length=128)
    branch: str = Field(default="main", min_length=1, max_length=255)
    requested_revision: str | None = Field(default=None, max_length=255)
    idempotency_key: str | None = Field(default=None, min_length=1, max_length=255)


def _error(code: str, message: str, status_code: int) -> HTTPException:
    return HTTPException(status_code=status_code, detail={"code": code, "message": message})


def _job_payload(job: ConnectorIngestionJob) -> dict[str, Any]:
    return {
        "connection_id": job.connection_id,
        "job_id": job.id,
        "status": job.state,
        "stage": job.stage,
        "progress": job.progress_percent,
        "files_discovered": job.files_discovered,
        "files_processed": job.files_processed,
        "nodes_written": job.nodes_written,
        "edges_written": job.edges_written,
        "attempt": job.attempt,
        "cancellation_requested": job.cancellation_requested,
        "error": (
            {"code": job.error_code, "message": job.error_summary}
            if job.error_code or job.error_summary
            else None
        ),
        "created_at": job.created_at.isoformat(),
        "updated_at": job.updated_at.isoformat(),
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "status_url": f"/api/connector-ingestions/{job.id}",
    }


def _has_inline_access_token(connection: dict[str, object]) -> bool:
    raw = connection.get("config") or {}
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except (TypeError, json.JSONDecodeError):
            return False
    return isinstance(raw, dict) and bool(raw.get("access_token"))


async def _enqueue(job: ConnectorIngestionJob) -> None:
    """Publish IDs only and fail quickly when Redis is unavailable."""
    redis = Redis.from_url(
        get_settings().redis_url,
        decode_responses=False,
        socket_connect_timeout=1,
        socket_timeout=2,
    )
    try:
        await redis.ping()
        queue = IngestionQueue(redis, consumer="api-submitter")
        await queue.ensure_group()
        await queue.enqueue(job.id, job.organization_id)
    finally:
        await redis.aclose()


async def _parallel_workers_ready() -> bool:
    """Fail closed unless the declared parallel topology is live."""
    settings = get_settings()
    redis = Redis.from_url(
        settings.redis_url,
        decode_responses=False,
        socket_connect_timeout=1,
        socket_timeout=2,
    )
    try:
        counts: dict[str, int] = {}
        for role, prefix in {
            "coordinator": "ecms:connector-ingestion:coordinator-health:",
            "extractor": "ecms:connector-ingestion:extractor-health:",
            "writer": "ecms:connector-ingestion:graph-writer-health:",
        }.items():
            count = 0
            async for _key in redis.scan_iter(match=f"{prefix}*", count=50):
                count += 1
            counts[role] = count
        return (
            counts["coordinator"] >= 1
            and counts["extractor"] >= settings.connector_extraction_worker_count
            and counts["writer"] >= settings.connector_graph_writer_concurrency
        )
    except Exception:
        return False
    finally:
        await redis.aclose()


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def submit_ingestion(
    body: SubmitIngestion,
    identity: Annotated[Identity, Depends(require_graph_identity)],
) -> dict[str, Any]:
    """Create or coalesce a job and return without doing repository work."""
    if not get_settings().connector_ingestion_enabled:
        raise _error(
            "CONNECTOR_INGESTION_DISABLED",
            "Connector ingestion is temporarily disabled",
            503,
        )
    if get_settings().connector_parallel_ingestion_enabled and not await _parallel_workers_ready():
        raise _error(
            "PARALLEL_INGESTION_UNAVAILABLE",
            "Parallel connector workers have not reached configured capacity",
            503,
        )
    organization_id = _organization_id(identity)
    async with db_session() as session:
        repository = ConnectorIngestionJobRepository(session)
        connection = await repository.owned_connection(
            body.connection_id, owner_email=identity.subject
        )
        if connection is None:
            raise _error("CONNECTION_NOT_FOUND", "Connection was not found", 404)
        provider = str(connection.get("provider") or "").lower()
        if provider not in {"git", "github", "gitlab", "bitbucket"}:
            raise _error("UNSUPPORTED_CONNECTOR", "Connection is not source control", 422)
        # Initial rollout deliberately supports public repositories only. Tokens
        # must not be copied from legacy plaintext config into jobs or Redis.
        if _has_inline_access_token(connection):
            raise _error(
                "PRIVATE_REPOSITORY_NOT_SUPPORTED",
                "Private repository ingestion requires managed secret storage",
                422,
            )
        repository_url = str(connection.get("repo_url") or "").strip()
        service = ConnectorIngestionService(repository)
        try:
            job, created = await service.submit(
                organization_id=organization_id,
                workspace_id=body.workspace_id,
                connection_id=body.connection_id,
                repository_url=repository_url,
                branch=body.branch,
                requested_revision=body.requested_revision,
                idempotency_key=body.idempotency_key,
            )
        except ValueError as exc:
            raise _error("INVALID_INGESTION_REQUEST", str(exc), 422) from exc

    if created:
        try:
            await _enqueue(job)
        except Exception as exc:
            async with db_session() as session:
                repository = ConnectorIngestionJobRepository(session)
                persisted = await repository.get(job.id, organization_id)
                if persisted is not None:
                    await ConnectorIngestionService(repository).transition(
                        persisted,
                        "failed",
                        error_code="QUEUE_UNAVAILABLE",
                        error_summary="Connector ingestion queue is unavailable",
                    )
            raise _error(
                "QUEUE_UNAVAILABLE",
                "Connector ingestion queue is temporarily unavailable",
                503,
            ) from exc
    return _job_payload(job)


@router.get("/{job_id}")
async def get_ingestion(
    job_id: str,
    identity: Annotated[Identity, Depends(require_graph_identity)],
) -> dict[str, Any]:
    """Return tenant-scoped durable progress for one ingestion."""
    async with db_session() as session:
        job = await ConnectorIngestionJobRepository(session).get(job_id, _organization_id(identity))
        if job is None:
            raise _error("INGESTION_NOT_FOUND", "Ingestion job was not found", 404)
        payload = _job_payload(job)
        if get_settings().connector_parallel_ingestion_enabled:
            partitions = await ConnectorIngestionPartitionRepository(session).reconcile(
                job.id,
                job.organization_id,
            )
            batches = await ConnectorIngestionStageBatchRepository(session).reconcile(
                job.id,
                job.organization_id,
            )
            payload["parallel"] = {
                "enabled": True,
                "partitions": partitions,
                "stage_batches": batches,
                "extraction_worker_target": (get_settings().connector_extraction_worker_count),
                "graph_writer_concurrency": (get_settings().connector_graph_writer_concurrency),
            }
        else:
            payload["parallel"] = {"enabled": False}
        return payload


@router.post("/{job_id}/cancel", status_code=status.HTTP_202_ACCEPTED)
async def cancel_ingestion(
    job_id: str,
    identity: Annotated[Identity, Depends(require_graph_identity)],
) -> dict[str, Any]:
    """Request cooperative cancellation without waiting for the worker."""
    organization_id = _organization_id(identity)
    async with db_session() as session:
        repository = ConnectorIngestionJobRepository(session)
        job = await repository.get(job_id, organization_id)
        if job is None:
            raise _error("INGESTION_NOT_FOUND", "Ingestion job was not found", 404)
        try:
            if get_settings().connector_parallel_ingestion_enabled:
                job = await repository.cancel_job_tree(job.id, organization_id)
            else:
                await ConnectorIngestionService(repository).request_cancellation(job)
        except ValueError as exc:
            raise _error("INGESTION_NOT_CANCELLABLE", str(exc), 409) from exc
        return _job_payload(job)


@router.post("/{job_id}/retry", status_code=status.HTTP_202_ACCEPTED)
async def retry_ingestion(
    job_id: str,
    identity: Annotated[Identity, Depends(require_graph_identity)],
) -> dict[str, Any]:
    """Create and enqueue a new attempt for a terminal failed job."""
    organization_id = _organization_id(identity)
    async with db_session() as session:
        repository = ConnectorIngestionJobRepository(session)
        failed = await repository.get(job_id, organization_id)
        if failed is None:
            raise _error("INGESTION_NOT_FOUND", "Ingestion job was not found", 404)
        try:
            job = await ConnectorIngestionService(repository).retry(failed)
        except ValueError as exc:
            raise _error("INGESTION_NOT_RETRYABLE", str(exc), 409) from exc
    try:
        await _enqueue(job)
    except Exception as exc:
        async with db_session() as session:
            repository = ConnectorIngestionJobRepository(session)
            persisted = await repository.get(job.id, organization_id)
            if persisted is not None:
                await ConnectorIngestionService(repository).transition(
                    persisted,
                    "failed",
                    error_code="QUEUE_UNAVAILABLE",
                    error_summary="Connector ingestion queue is unavailable",
                )
        raise _error(
            "QUEUE_UNAVAILABLE", "Connector ingestion queue is temporarily unavailable", 503
        ) from exc
    return _job_payload(job)

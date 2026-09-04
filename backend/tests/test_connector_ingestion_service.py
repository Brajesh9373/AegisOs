from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from ecms.connectors.ingestion.service import (
    ConnectorIngestionService,
    normalize_repository_identity,
)
from ecms.persistence.models.connector_ingestion_job import ConnectorIngestionJob
from ecms.persistence.repositories.connector_ingestion_job import (
    ConnectorIngestionJobRepository,
)


async def _factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(ConnectorIngestionJob.__table__.create)
        await connection.execute(
            text(
                "CREATE TABLE connections ("
                "number INTEGER PRIMARY KEY, organization_id TEXT, sync_state TEXT, "
                "current_ingestion_job_id TEXT, last_error_summary TEXT)"
            )
        )
        await connection.execute(text("INSERT INTO connections(number) VALUES (7)"))
    return engine, async_sessionmaker(engine, expire_on_commit=False)


async def _submit(service: ConnectorIngestionService):
    return await service.submit(
        organization_id="org-1",
        workspace_id=None,
        connection_id=7,
        repository_url="https://github.com/OpenClaw/OpenClaw.git",
        branch="main",
        requested_revision=None,
        idempotency_key=None,
    )


def test_repository_identity_removes_credentials_and_git_suffix() -> None:
    with pytest.raises(ValueError, match="must not contain credentials"):
        normalize_repository_identity("https://token@GitHub.com/OpenClaw/OpenClaw.git?private=1")
    assert (
        normalize_repository_identity("git@github.com:OpenClaw/OpenClaw.git")
        == "ssh://github.com/OpenClaw/OpenClaw"
    )


@pytest.mark.asyncio
async def test_duplicate_active_submission_is_coalesced() -> None:
    engine, factory = await _factory()
    async with factory() as session:
        service = ConnectorIngestionService(ConnectorIngestionJobRepository(session))
        first, first_created = await _submit(service)
        duplicate, duplicate_created = await _submit(service)
        await session.commit()
    assert first_created is True
    assert duplicate_created is False
    assert duplicate.id == first.id
    assert first.repository_url == "https://github.com/OpenClaw/OpenClaw.git"
    assert first.repository_identity == "https://github.com/OpenClaw/OpenClaw"
    await engine.dispose()


@pytest.mark.asyncio
async def test_illegal_transition_is_rejected_and_terminal_invariants_hold() -> None:
    engine, factory = await _factory()
    async with factory() as session:
        repository = ConnectorIngestionJobRepository(session)
        service = ConnectorIngestionService(repository)
        job, _ = await _submit(service)
        with pytest.raises(ValueError, match="queued -> ready"):
            await service.transition(job, "ready")
        await service.transition(job, "failed", error_summary="clone timed out")
        await session.commit()
    assert job.completed_at is not None
    assert job.lease_owner is None
    assert job.error_code == "INGESTION_FAILED"
    assert job.error_summary == "clone timed out"
    await engine.dispose()


@pytest.mark.asyncio
async def test_cancellation_is_idempotent_and_failed_job_can_retry() -> None:
    engine, factory = await _factory()
    async with factory() as session:
        repository = ConnectorIngestionJobRepository(session)
        service = ConnectorIngestionService(repository)
        job, _ = await _submit(service)
        cancelled = await service.request_cancellation(job)
        same = await service.request_cancellation(job)
        assert same.id == cancelled.id
        await service.transition(job, "cancelled")
        retried = await service.retry(job)
        await session.commit()
    assert retried.id != job.id
    assert retried.attempt == 1
    assert retried.state == "queued"
    assert retried.cancellation_requested is False
    await engine.dispose()


@pytest.mark.asyncio
async def test_idempotency_key_returns_original_terminal_job() -> None:
    engine, factory = await _factory()
    async with factory() as session:
        repository = ConnectorIngestionJobRepository(session)
        service = ConnectorIngestionService(repository)
        first, created = await service.submit(
            organization_id="org-1",
            workspace_id=None,
            connection_id=7,
            repository_url="https://github.com/openclaw/openclaw",
            branch="main",
            requested_revision=None,
            idempotency_key="request-42",
        )
        await service.transition(first, "failed")
        repeated, repeated_created = await service.submit(
            organization_id="org-1",
            workspace_id=None,
            connection_id=7,
            repository_url="https://github.com/openclaw/openclaw",
            branch="main",
            requested_revision=None,
            idempotency_key="request-42",
        )
    assert created is True
    assert repeated_created is False
    assert repeated.id == first.id
    await engine.dispose()

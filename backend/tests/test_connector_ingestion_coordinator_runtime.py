from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from ecms.connectors.ingestion.coordinator import IngestionPlan, plan_repository
from ecms.connectors.ingestion.coordinator_runtime import (
    ConnectorIngestionCoordinator,
    PersistedPartition,
    SqlCoordinatorPlanStore,
    iter_stored_manifest,
)
from ecms.connectors.ingestion.scanner import ScanLimits
from ecms.connectors.ingestion.worker import GitJobSpec
from ecms.infrastructure.storage.object_store import InMemoryObjectStore
from ecms.persistence.models.connector_ingestion_job import ConnectorIngestionJob
from ecms.persistence.models.connector_ingestion_partition import (
    ConnectorIngestionManifest,
    ConnectorIngestionPartition,
)


class FakeWorkspace:
    def __init__(self, repository: Path, revision: str = "a" * 40) -> None:
        self.repository = repository
        self.revision = revision
        self.prepares = 0

    async def prepare(self, **_kwargs) -> Path:
        self.prepares += 1
        return self.repository

    async def current_revision(self, _repository: Path, **_kwargs) -> str:
        return self.revision


class FakeJobs:
    def __init__(self, spec: GitJobSpec) -> None:
        self.spec = spec
        self.stages: list[str] = []
        self.completed = 0
        self.cancelled = 0
        self.failures: list[tuple[str, bool]] = []
        self.cancel_requested = False

    async def claim(self, _job_id: str, _organization_id: str):
        return self.spec

    async def cancellation_requested(self, _job_id: str) -> bool:
        return self.cancel_requested

    async def renew_lease(self, _job_id: str) -> bool:
        return True

    async def mark_stage(self, _job_id: str, stage: str) -> None:
        self.stages.append(stage)

    async def record_revision(self, _job_id: str, revision: str) -> None:
        pass

    async def checkpoint(self, *_args, **_kwargs) -> None:
        pass

    async def complete(self, _job_id: str) -> None:
        self.completed += 1

    async def cancel(self, _job_id: str) -> None:
        self.cancelled += 1

    async def fail(self, _job_id: str, error: str, *, retrying: bool) -> None:
        self.failures.append((error, retrying))


class FakePlans:
    def __init__(self) -> None:
        self.calls: list[tuple[str, IngestionPlan, str]] = []

    async def persist(self, spec, *, revision, plan, object_key):
        self.calls.append((revision, plan, object_key))
        return tuple(
            PersistedPartition(
                partition_id=f"partition-{partition.index}",
                manifest_id="manifest-1",
                job_id=spec.job_id,
            )
            for partition in plan.partitions
            if partition.entries
        )


class FakePublisher:
    def __init__(self) -> None:
        self.messages: list[dict[str, str]] = []

    async def enqueue(self, **identifiers: str) -> str:
        self.messages.append(identifiers)
        return str(len(self.messages))


def _spec(*, last_revision: str | None = None) -> GitJobSpec:
    return GitJobSpec(
        job_id="job-1",
        organization_id="org/../../unsafe",
        repo_url="https://example.test/repo.git",
        branch="main",
        connection_id=1,
        last_successful_revision=last_revision,
    )


def _coordinator(tmp_path: Path, *, spec: GitJobSpec):
    repository = tmp_path / "source"
    repository.mkdir()
    (repository / "large.py").write_bytes(b"x" * 100)
    (repository / "small.md").write_bytes(b"# small")
    jobs = FakeJobs(spec)
    plans = FakePlans()
    publisher = FakePublisher()
    objects = InMemoryObjectStore()
    coordinator = ConnectorIngestionCoordinator(
        jobs=jobs,
        plans=plans,
        publisher=publisher,
        object_store=objects,
        workspace=FakeWorkspace(repository),  # type: ignore[arg-type]
        workspace_root=tmp_path / "workspaces",
        scan_limits=ScanLimits(),
        partition_count=2,
    )
    return coordinator, jobs, plans, publisher, objects


async def test_coordinator_clones_once_stores_plan_and_publishes_ids(tmp_path: Path) -> None:
    coordinator, jobs, plans, publisher, objects = _coordinator(tmp_path, spec=_spec())

    result = await coordinator.coordinate(job_id="job-1", organization_id="org")

    assert result is not None and result.status == "partitioned"
    assert result.partition_count == 2
    assert jobs.stages == ["cloning", "scanning"]
    assert len(plans.calls) == 1
    assert publisher.messages == [
        {
            "job_id": "job-1",
            "manifest_id": "manifest-1",
            "partition_id": "partition-0",
        },
        {
            "job_id": "job-1",
            "manifest_id": "manifest-1",
            "partition_id": "partition-1",
        },
    ]
    keys = await objects.list_objects("connector-ingestion/manifests/")
    assert len(keys) == 1
    records = [record async for record in iter_stored_manifest(objects, keys[0])]
    assert records[0]["format"] == "ecms.connector-manifest.v1"
    assert records[0]["file_count"] == 2
    assert {record["relative_path"] for record in records[1:]} == {
        "large.py",
        "small.md",
    }
    assert all("partition_index" in record for record in records[1:])


async def test_coordinator_short_circuits_unchanged_revision(tmp_path: Path) -> None:
    coordinator, jobs, plans, publisher, objects = _coordinator(
        tmp_path, spec=_spec(last_revision="a" * 40)
    )

    result = await coordinator.coordinate(job_id="job-1", organization_id="org")

    assert result is not None and result.status == "unchanged"
    assert jobs.completed == 1
    assert plans.calls == []
    assert publisher.messages == []
    assert await objects.list_objects() == []


async def test_coordinator_cancels_before_clone_when_lease_is_lost(
    tmp_path: Path,
) -> None:
    coordinator, jobs, plans, publisher, _objects = _coordinator(tmp_path, spec=_spec())

    async def lease_lost(_job_id: str) -> bool:
        return False

    async def slow_prepare(**_kwargs) -> Path:
        await asyncio.sleep(0.01)
        return tmp_path / "source"

    jobs.renew_lease = lease_lost  # type: ignore[method-assign]
    coordinator._workspace.prepare = slow_prepare  # type: ignore[method-assign,union-attr]
    result = await coordinator.coordinate(job_id="job-1", organization_id="org")

    assert result is not None and result.status == "cancelled"
    assert jobs.cancelled == 1
    assert plans.calls == []
    assert publisher.messages == []


async def test_coordinator_marks_retryable_failure(tmp_path: Path) -> None:
    coordinator, jobs, _plans, _publisher, _objects = _coordinator(tmp_path, spec=_spec())
    coordinator._workspace = FakeWorkspace(  # type: ignore[attr-defined]
        tmp_path / "missing"
    )

    with pytest.raises(RuntimeError, match="empty manifest"):
        await coordinator.coordinate(job_id="job-1", organization_id="org")

    assert len(jobs.failures) == 1
    assert jobs.failures[0][1] is True
    assert "empty manifest" in jobs.failures[0][0]


async def test_sql_plan_store_is_idempotent_and_recovers_for_publication(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    (repository / "a.py").write_bytes(b"a" * 20)
    (repository / "b.py").write_bytes(b"b" * 10)
    plan = await plan_repository(
        repository,
        limits=ScanLimits(),
        partition_count=2,
        cancel=asyncio.Event(),
    )
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        for table in (
            ConnectorIngestionJob.__table__,
            ConnectorIngestionManifest.__table__,
            ConnectorIngestionPartition.__table__,
        ):
            await connection.run_sync(table.create)
    async with factory() as session:
        session.add(
            ConnectorIngestionJob(
                id="job-1",
                organization_id="org/../../unsafe",
                connection_id=1,
                repository_identity="repo",
                repository_url="https://example.test/repo.git",
                branch="main",
                state="scanning",
                stage="scanning",
            )
        )
        await session.commit()

    @asynccontextmanager
    async def sessions():
        async with factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    store = SqlCoordinatorPlanStore(sessions)
    spec = _spec()
    first = await store.persist(
        spec,
        revision="a" * 40,
        plan=plan,
        object_key="manifest.jsonl.gz",
    )
    replay = await store.persist(
        spec,
        revision="a" * 40,
        plan=plan,
        object_key="manifest.jsonl.gz",
    )

    assert replay == first
    async with factory() as session:
        assert await session.scalar(select(func.count(ConnectorIngestionManifest.id))) == 1
        assert await session.scalar(select(func.count(ConnectorIngestionPartition.id))) == 2
        job = await session.get(ConnectorIngestionJob, "job-1")
        assert job is not None
        assert job.state == job.stage == "extracting"
        assert job.files_discovered == 2
        assert job.checkpoint["manifest_checksum"] == plan.manifest.checksum
    await engine.dispose()

"""Worker orchestration regressions for incremental connector ingestion."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import falkordb
import pytest

from ecms.connectors.ingestion.queue import IngestionJob
from ecms.connectors.ingestion.worker import (
    GitJobSpec,
    IngestionWorker,
    LegacyGraphChunkSink,
)


class _Queue:
    def __init__(self, *, fail_acknowledgement: bool = False) -> None:
        self.acknowledged = False
        self.fail_acknowledgement = fail_acknowledgement

    async def acknowledge(self, _delivery: IngestionJob) -> None:
        if self.fail_acknowledgement:
            raise ConnectionError("Redis unavailable")
        self.acknowledged = True

    async def set_metric(self, _name: str, _value: float) -> None:
        return None

    async def retry_or_exhaust(self, _delivery: IngestionJob, *, max_deliveries: int) -> bool:
        return max_deliveries > 1


class _Store:
    def __init__(self, spec: GitJobSpec) -> None:
        self.spec = spec
        self.stages: list[str] = []
        self.completed = False

    async def claim(self, _job_id: str, _organization_id: str) -> GitJobSpec:
        return self.spec

    async def renew_lease(self, _job_id: str) -> bool:
        return True

    async def cancellation_requested(self, _job_id: str) -> bool:
        return False

    async def mark_stage(self, _job_id: str, stage: str) -> None:
        self.stages.append(stage)

    async def record_revision(self, _job_id: str, _revision: str) -> None:
        return None

    async def complete(self, _job_id: str) -> None:
        self.completed = True

    async def checkpoint(self, *_args: object, **_kwargs: object) -> None:
        raise AssertionError("unchanged revision must not scan or checkpoint")

    async def cancel(self, _job_id: str) -> None:
        raise AssertionError("unchanged revision must not cancel")

    async def fail(self, _job_id: str, _error: str, *, retrying: bool) -> None:
        raise AssertionError(f"unchanged revision must not fail: retrying={retrying}")


class _Workspace:
    def __init__(self, repository: Path) -> None:
        self._repository = repository

    async def prepare(self, **_kwargs: object) -> Path:
        return self._repository

    async def current_revision(self, _repository: Path, **_kwargs: object) -> str:
        return "abc123"


class _Sink:
    async def write(self, *_args: object, **_kwargs: object) -> object:
        raise AssertionError("unchanged revision must not write")

    async def finalize(self, *_args: object, **_kwargs: object) -> None:
        raise AssertionError("unchanged revision must not snapshot")


@pytest.mark.asyncio
async def test_unchanged_revision_completes_without_graph_rewrite(
    tmp_path: Path,
) -> None:
    spec = GitJobSpec(
        job_id="job-1",
        organization_id="org-1",
        repo_url="https://example.com/acme/repo",
        branch="main",
        connection_id=7,
        last_successful_revision="abc123",
    )
    queue = _Queue()
    store = _Store(spec)
    settings = SimpleNamespace(
        connector_git_clone_timeout_seconds=10,
        connector_git_fetch_timeout_seconds=10,
        connector_git_clone_depth=1,
        connector_ingestion_workspace=str(tmp_path),
        connector_ingestion_max_deliveries=3,
    )
    worker = IngestionWorker(
        queue=queue,  # type: ignore[arg-type]
        store=store,
        sink=_Sink(),
        settings=settings,  # type: ignore[arg-type]
    )
    worker._workspace = _Workspace(tmp_path / "repository")  # type: ignore[assignment]

    await worker.process(IngestionJob(message_id="1-0", job_id="job-1", organization_id="org-1"))

    assert store.stages == ["cloning"]
    assert store.completed is True
    assert queue.acknowledged is True


@pytest.mark.asyncio
async def test_terminal_database_state_survives_redis_ack_outage(
    tmp_path: Path,
) -> None:
    spec = GitJobSpec(
        job_id="job-2",
        organization_id="org-1",
        repo_url="https://example.com/acme/repo",
        branch="main",
        connection_id=7,
        last_successful_revision="abc123",
    )
    queue = _Queue(fail_acknowledgement=True)
    store = _Store(spec)
    settings = SimpleNamespace(
        connector_git_clone_timeout_seconds=10,
        connector_git_fetch_timeout_seconds=10,
        connector_git_clone_depth=1,
        connector_ingestion_workspace=str(tmp_path),
        connector_ingestion_max_deliveries=3,
    )
    worker = IngestionWorker(
        queue=queue,  # type: ignore[arg-type]
        store=store,
        sink=_Sink(),
        settings=settings,  # type: ignore[arg-type]
    )
    worker._workspace = _Workspace(tmp_path / "repository")  # type: ignore[assignment]

    await worker.process(IngestionJob(message_id="2-0", job_id="job-2", organization_id="org-1"))

    assert store.completed is True
    assert queue.acknowledged is False


def test_stale_revision_cleanup_is_bounded_and_tenant_scoped(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, dict[str, object]]] = []

    class _Result:
        def __init__(self, deleted: int) -> None:
            self.result_set = [[deleted]]

    class _Graph:
        def query(self, query: str, parameters: dict[str, object]) -> _Result:
            calls.append((query, parameters))
            return _Result(10_000 if len(calls) == 1 else 2)

    graph = _Graph()
    monkeypatch.setattr(
        falkordb,
        "FalkorDB",
        lambda **_kwargs: SimpleNamespace(select_graph=lambda _name: graph),
    )

    LegacyGraphChunkSink._retire_stale_revision(
        GitJobSpec(
            job_id="job-3",
            organization_id="org-9",
            repo_url="https://example.com/acme/repo",
            branch="main",
            connection_id=42,
            resolved_revision="def456",
        )
    )

    assert len(calls) == 2
    assert "u.organization_id = $organization_id" in calls[0][0]
    assert "u.connection_id = $connection_id" in calls[0][0]
    assert calls[0][1] == {
        "organization_id": "org-9",
        "connection_id": "42",
        "revision": "def456",
        "batch_size": 10_000,
    }

from __future__ import annotations

from datetime import timedelta

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from ecms.persistence.models.connector_ingestion_job import ConnectorIngestionJob
from ecms.persistence.models.connector_ingestion_partition import (
    ConnectorIngestionManifest,
    ConnectorIngestionPartition,
    ConnectorIngestionStageBatch,
)
from ecms.persistence.repositories.connector_ingestion_job import (
    ConnectorIngestionJobRepository,
)
from ecms.persistence.repositories.connector_ingestion_partition import (
    ConnectorIngestionManifestRepository,
    ConnectorIngestionPartitionRepository,
    ConnectorIngestionStageBatchRepository,
)
from ecms.shared.time import utcnow


async def _factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.execute(text("PRAGMA foreign_keys=ON"))
        for table in (
            ConnectorIngestionJob.__table__,
            ConnectorIngestionManifest.__table__,
            ConnectorIngestionPartition.__table__,
            ConnectorIngestionStageBatch.__table__,
        ):
            await connection.run_sync(table.create)
        await connection.execute(
            text(
                "CREATE TABLE connections ("
                "number INTEGER PRIMARY KEY, organization_id TEXT, sync_state TEXT, "
                "current_ingestion_job_id TEXT, last_error_summary TEXT)"
            )
        )
    return engine, async_sessionmaker(engine, expire_on_commit=False)


def _job() -> ConnectorIngestionJob:
    return ConnectorIngestionJob(
        id="job-1",
        organization_id="org-1",
        connection_id=7,
        repository_identity="https://github.com/acme/repo",
        repository_url="https://github.com/acme/repo",
        branch="main",
        state="queued",
        stage="queued",
    )


def _manifest() -> ConnectorIngestionManifest:
    return ConnectorIngestionManifest(
        id="manifest-1",
        job_id="job-1",
        organization_id="org-1",
        resolved_revision="abc123",
        checksum="a" * 64,
        file_count=8,
        total_weight=800,
        partition_count=2,
    )


@pytest.mark.asyncio
async def test_manifest_is_one_per_job_and_has_guarded_terminal_transition() -> None:
    engine, factory = await _factory()
    async with factory() as session:
        session.add(_job())
        repository = ConnectorIngestionManifestRepository(session)
        manifest = await repository.add(_manifest())
        await repository.transition(manifest, "ready")
        assert manifest.completed_at is not None
        with pytest.raises(ValueError, match="ready -> failed"):
            await repository.transition(manifest, "failed")
        session.add(
            ConnectorIngestionManifest(
                id="manifest-2",
                job_id="job-1",
                organization_id="org-1",
                resolved_revision="different",
                checksum="b" * 64,
            )
        )
        with pytest.raises(IntegrityError):
            await session.flush()
    await engine.dispose()


@pytest.mark.asyncio
async def test_partition_claim_is_exclusive_and_prefers_largest_weight() -> None:
    engine, factory = await _factory()
    async with factory() as session:
        session.add(_job())
        session.add(_manifest())
        repository = ConnectorIngestionPartitionRepository(session)
        await repository.add_all(
            [
                ConnectorIngestionPartition(
                    id="partition-0",
                    manifest_id="manifest-1",
                    job_id="job-1",
                    organization_id="org-1",
                    partition_number=0,
                    estimated_weight=100,
                ),
                ConnectorIngestionPartition(
                    id="partition-1",
                    manifest_id="manifest-1",
                    job_id="job-1",
                    organization_id="org-1",
                    partition_number=1,
                    estimated_weight=700,
                ),
            ]
        )
        first = await repository.claim_next(
            job_id="job-1",
            organization_id="org-1",
            worker_id="worker-a",
            lease_seconds=60,
        )
        second = await repository.claim_next(
            job_id="job-1",
            organization_id="org-1",
            worker_id="worker-b",
            lease_seconds=60,
        )
        assert first is not None and first.id == "partition-1"
        assert second is not None and second.id == "partition-0"
        assert first.lease_owner == "worker-a"
        with pytest.raises(ValueError, match="lease is not owned"):
            await repository.transition(first, "extracting", worker_id="worker-b")
        await repository.transition(first, "extracting", worker_id="worker-a")
        await repository.transition(first, "staged", worker_id="worker-a")
        await repository.transition(first, "committed", worker_id="worker-a")
        assert first.lease_owner is None
        assert await repository.state_counts("job-1", "org-1") == {
            "claimed": 1,
            "committed": 1,
        }
    await engine.dispose()


@pytest.mark.asyncio
async def test_expired_partition_lease_can_be_reclaimed() -> None:
    engine, factory = await _factory()
    now = utcnow()
    async with factory() as session:
        session.add(_job())
        session.add(_manifest())
        session.add(
            ConnectorIngestionPartition(
                id="partition-0",
                manifest_id="manifest-1",
                job_id="job-1",
                organization_id="org-1",
                partition_number=0,
                state="claimed",
                lease_owner="dead-worker",
                lease_expires_at=now - timedelta(seconds=1),
            )
        )
        await session.flush()
        reclaimed = await ConnectorIngestionPartitionRepository(session).claim_next(
            job_id="job-1",
            organization_id="org-1",
            worker_id="worker-b",
            lease_seconds=30,
            now=now,
        )
        assert reclaimed is not None
        assert reclaimed.lease_owner == "worker-b"
        assert reclaimed.attempt == 1
    await engine.dispose()


@pytest.mark.asyncio
async def test_stage_batch_checksum_is_idempotent_and_write_is_guarded() -> None:
    engine, factory = await _factory()
    async with factory() as session:
        session.add(_job())
        session.add(_manifest())
        session.add(
            ConnectorIngestionPartition(
                id="partition-0",
                manifest_id="manifest-1",
                job_id="job-1",
                organization_id="org-1",
                partition_number=0,
            )
        )
        repository = ConnectorIngestionStageBatchRepository(session)
        batch = await repository.add(
            ConnectorIngestionStageBatch(
                id="batch-1",
                partition_id="partition-0",
                job_id="job-1",
                organization_id="org-1",
                sequence_number=0,
                checksum="c" * 64,
                object_key="staging/org-1/job-1/partition-0/0.parquet",
                node_count=12,
                edge_count=20,
            )
        )
        assert await repository.get_by_checksum("partition-0", "c" * 64) is batch
        with pytest.raises(ValueError, match="writer_id is required"):
            await repository.transition(batch, "writing")
        await repository.transition(batch, "writing", writer_id="writer-a")
        with pytest.raises(ValueError, match="another writer"):
            await repository.transition(batch, "committed", writer_id="writer-b")
        await repository.transition(batch, "committed", writer_id="writer-a")
        assert batch.committed_at is not None
        assert batch.writer_owner is None
    await engine.dispose()


@pytest.mark.asyncio
async def test_partition_lookup_renewal_checkpoint_and_tenant_boundary() -> None:
    engine, factory = await _factory()
    now = utcnow()
    async with factory() as session:
        session.add(_job())
        session.add(_manifest())
        repository = ConnectorIngestionPartitionRepository(session)
        await repository.add_all(
            [
                ConnectorIngestionPartition(
                    id="partition-0",
                    manifest_id="manifest-1",
                    job_id="job-1",
                    organization_id="org-1",
                    partition_number=0,
                )
            ]
        )
        partition = await repository.claim_next(
            job_id="job-1",
            organization_id="org-1",
            worker_id="worker-a",
            lease_seconds=30,
            now=now,
        )
        assert partition is not None
        assert await repository.get("partition-0", "other-org") is None
        assert await repository.renew_lease(
            "partition-0",
            organization_id="org-1",
            worker_id="worker-a",
            lease_seconds=60,
            now=now + timedelta(seconds=10),
        )
        assert not await repository.renew_lease(
            "partition-0",
            organization_id="org-1",
            worker_id="worker-b",
            lease_seconds=60,
            now=now + timedelta(seconds=10),
        )
        await repository.transition(partition, "extracting", worker_id="worker-a")
        await repository.update_checkpoint(
            partition,
            worker_id="worker-a",
            checkpoint={"last_path": "src/b.py"},
            files_processed=3,
            nodes_extracted=7,
            edges_extracted=9,
        )
        await repository.update_checkpoint(
            partition,
            worker_id="worker-a",
            checkpoint={"cursor": 3},
            files_processed=2,
        )
        assert partition.checkpoint == {"last_path": "src/b.py", "cursor": 3}
        assert partition.files_processed == 3
        with pytest.raises(ValueError, match="lease is not owned"):
            await repository.update_checkpoint(
                partition, worker_id="worker-b", checkpoint={"cursor": 4}
            )
    await engine.dispose()


@pytest.mark.asyncio
async def test_batch_claim_renewal_and_expired_writer_recovery() -> None:
    engine, factory = await _factory()
    now = utcnow()
    async with factory() as session:
        session.add(_job())
        session.add(_manifest())
        session.add(
            ConnectorIngestionPartition(
                id="partition-0",
                manifest_id="manifest-1",
                job_id="job-1",
                organization_id="org-1",
                partition_number=0,
            )
        )
        repository = ConnectorIngestionStageBatchRepository(session)
        await repository.add(
            ConnectorIngestionStageBatch(
                id="batch-expired",
                partition_id="partition-0",
                job_id="job-1",
                organization_id="org-1",
                sequence_number=0,
                checksum="d" * 64,
                object_key="expired.parquet",
                state="writing",
                writer_owner="dead-writer",
                writer_lease_expires_at=now - timedelta(seconds=1),
            )
        )
        await repository.add(
            ConnectorIngestionStageBatch(
                id="batch-staged",
                partition_id="partition-0",
                job_id="job-1",
                organization_id="org-1",
                sequence_number=1,
                checksum="e" * 64,
                object_key="staged.parquet",
            )
        )
        first = await repository.claim_next(
            job_id="job-1",
            organization_id="org-1",
            writer_id="writer-a",
            lease_seconds=30,
            now=now,
        )
        assert first is not None and first.id == "batch-expired"
        assert first.writer_owner == "writer-a"
        assert first.attempt == 1
        assert await repository.get("batch-expired", "other-org") is None
        assert await repository.renew_lease(
            "batch-expired",
            organization_id="org-1",
            writer_id="writer-a",
            lease_seconds=60,
            now=now + timedelta(seconds=10),
        )
        assert not await repository.renew_lease(
            "batch-expired",
            organization_id="org-1",
            writer_id="writer-b",
            lease_seconds=60,
            now=now + timedelta(seconds=10),
        )
        second = await repository.claim_next(
            job_id="job-1",
            organization_id="org-1",
            writer_id="writer-b",
            lease_seconds=30,
            now=now,
        )
        assert second is not None and second.id == "batch-staged"
    await engine.dispose()


@pytest.mark.asyncio
async def test_reconciliation_and_cancellation_are_authoritative_and_idempotent() -> None:
    engine, factory = await _factory()
    async with factory() as session:
        session.add(_job())
        session.add(_manifest())
        partitions = ConnectorIngestionPartitionRepository(session)
        await partitions.add_all(
            [
                ConnectorIngestionPartition(
                    id="partition-0",
                    manifest_id="manifest-1",
                    job_id="job-1",
                    organization_id="org-1",
                    partition_number=0,
                    state="committed",
                    file_count=2,
                    files_processed=2,
                    nodes_extracted=5,
                    edges_extracted=6,
                ),
                ConnectorIngestionPartition(
                    id="partition-1",
                    manifest_id="manifest-1",
                    job_id="job-1",
                    organization_id="org-1",
                    partition_number=1,
                    state="extracting",
                    lease_owner="worker-a",
                    file_count=3,
                    files_processed=1,
                    nodes_extracted=2,
                    edges_extracted=1,
                ),
            ]
        )
        batches = ConnectorIngestionStageBatchRepository(session)
        await batches.add(
            ConnectorIngestionStageBatch(
                id="batch-0",
                partition_id="partition-0",
                job_id="job-1",
                organization_id="org-1",
                sequence_number=0,
                checksum="f" * 64,
                object_key="committed.parquet",
                state="committed",
                node_count=5,
                edge_count=6,
                byte_count=100,
            )
        )
        await batches.add(
            ConnectorIngestionStageBatch(
                id="batch-1",
                partition_id="partition-1",
                job_id="job-1",
                organization_id="org-1",
                sequence_number=0,
                checksum="0" * 64,
                object_key="writing.parquet",
                state="writing",
                writer_owner="writer-a",
                node_count=2,
                edge_count=1,
                byte_count=50,
            )
        )

        partition_summary = await partitions.reconcile("job-1", "org-1")
        assert partition_summary == {
            "states": {"committed": 1, "extracting": 1},
            "partition_count": 2,
            "file_count": 5,
            "files_processed": 3,
            "nodes_extracted": 7,
            "edges_extracted": 7,
            "all_committed": False,
            "has_failures": False,
        }
        batch_summary = await batches.reconcile("job-1", "org-1")
        assert batch_summary == {
            "states": {"committed": 1, "writing": 1},
            "batch_count": 2,
            "node_count": 7,
            "edge_count": 7,
            "byte_count": 150,
            "all_committed": False,
            "has_failures": False,
        }
        assert await partitions.cancel_for_job("job-1", "org-1") == 1
        assert await batches.cancel_for_job("job-1", "org-1") == 1
        assert await partitions.cancel_for_job("job-1", "org-1") == 0
        assert await batches.cancel_for_job("job-1", "org-1") == 0

        partition_rows = await partitions.list_for_job("job-1", "org-1")
        batch_rows = await batches.list_for_job("job-1", "org-1")
        assert [row.state for row in partition_rows] == ["committed", "cancelled"]
        assert [row.state for row in batch_rows] == ["committed", "cancelled"]
        assert partition_rows[1].lease_owner is None
        assert batch_rows[1].writer_owner is None
    await engine.dispose()


@pytest.mark.asyncio
async def test_same_revision_manifest_can_be_ingested_by_multiple_jobs() -> None:
    engine, factory = await _factory()
    async with factory() as session:
        first = _job()
        first.state = "failed"
        second = _job()
        second.id = "job-2"
        second.connection_id = 8
        second.state = "failed"
        session.add_all([first, second])
        session.add_all(
            [
                _manifest(),
                ConnectorIngestionManifest(
                    id="manifest-2",
                    job_id="job-2",
                    organization_id="org-1",
                    resolved_revision="abc123",
                    checksum="a" * 64,
                ),
            ]
        )
        await session.flush()
        assert (
            await ConnectorIngestionManifestRepository(session).get_for_job(
                "job-2", "org-1"
            )
        ) is not None
    await engine.dispose()


@pytest.mark.asyncio
async def test_composite_provenance_rejects_cross_job_partition() -> None:
    engine, factory = await _factory()
    async with factory() as session:
        session.add(_job())
        session.add(_manifest())
        await session.flush()
        session.add(
            ConnectorIngestionPartition(
                id="partition-invalid",
                manifest_id="manifest-1",
                job_id="job-1",
                organization_id="other-org",
                partition_number=0,
            )
        )
        with pytest.raises(IntegrityError):
            await session.flush()
    await engine.dispose()


@pytest.mark.asyncio
async def test_composite_provenance_rejects_cross_partition_stage_batch() -> None:
    engine, factory = await _factory()
    async with factory() as session:
        session.add(_job())
        session.add(_manifest())
        session.add(
            ConnectorIngestionPartition(
                id="partition-0",
                manifest_id="manifest-1",
                job_id="job-1",
                organization_id="org-1",
                partition_number=0,
            )
        )
        await session.flush()
        session.add(
            ConnectorIngestionStageBatch(
                id="batch-invalid",
                partition_id="partition-0",
                job_id="job-1",
                organization_id="other-org",
                sequence_number=0,
                checksum="3" * 64,
                object_key="invalid.parquet",
            )
        )
        with pytest.raises(IntegrityError):
            await session.flush()
    await engine.dispose()


@pytest.mark.asyncio
async def test_database_checks_reject_invalid_parent_state_and_counters() -> None:
    engine, factory = await _factory()
    async with factory() as session:
        invalid = _job()
        invalid.state = "unknown"
        invalid.files_processed = -1
        session.add(invalid)
        with pytest.raises(IntegrityError):
            await session.flush()
    await engine.dispose()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("model"),
    [
        ConnectorIngestionPartition(
            id="negative-partition",
            manifest_id="manifest-1",
            job_id="job-1",
            organization_id="org-1",
            partition_number=-1,
        ),
        ConnectorIngestionPartition(
            id="invalid-partition-state",
            manifest_id="manifest-1",
            job_id="job-1",
            organization_id="org-1",
            partition_number=0,
            state="unknown",
        ),
    ],
)
async def test_database_checks_reject_invalid_partition_values(
    model: ConnectorIngestionPartition,
) -> None:
    engine, factory = await _factory()
    async with factory() as session:
        session.add(_job())
        session.add(_manifest())
        session.add(model)
        with pytest.raises(IntegrityError):
            await session.flush()
    await engine.dispose()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("parent_state", "partition_state", "batch_state"),
    [
        ("extracting", "pending", "staged"),
        ("writing", "extracting", "writing"),
        ("snapshotting", "staged", "staged"),
    ],
)
async def test_cancel_job_tree_is_atomic_and_preserves_committed_rows(
    parent_state: str,
    partition_state: str,
    batch_state: str,
) -> None:
    engine, factory = await _factory()
    async with factory() as session:
        job = _job()
        job.state = job.stage = parent_state
        job.lease_owner = "parent-worker"
        session.add(job)
        session.add(_manifest())
        session.add_all(
            [
                ConnectorIngestionPartition(
                    id="partition-active",
                    manifest_id="manifest-1",
                    job_id="job-1",
                    organization_id="org-1",
                    partition_number=0,
                    state=partition_state,
                    lease_owner="extractor",
                ),
                ConnectorIngestionPartition(
                    id="partition-committed",
                    manifest_id="manifest-1",
                    job_id="job-1",
                    organization_id="org-1",
                    partition_number=1,
                    state="committed",
                ),
            ]
        )
        session.add_all(
            [
                ConnectorIngestionStageBatch(
                    id="batch-active",
                    partition_id="partition-active",
                    job_id="job-1",
                    organization_id="org-1",
                    sequence_number=0,
                    checksum="1" * 64,
                    object_key="active.parquet",
                    state=batch_state,
                    writer_owner="writer",
                ),
                ConnectorIngestionStageBatch(
                    id="batch-committed",
                    partition_id="partition-committed",
                    job_id="job-1",
                    organization_id="org-1",
                    sequence_number=0,
                    checksum="2" * 64,
                    object_key="committed.parquet",
                    state="committed",
                ),
            ]
        )
        await session.execute(
            text(
                "INSERT INTO connections(number, organization_id, sync_state, "
                "current_ingestion_job_id) VALUES (7, 'org-1', :state, 'job-1')"
            ),
            {"state": parent_state},
        )
        await session.flush()

        repository = ConnectorIngestionJobRepository(session)
        cancelled = await repository.cancel_job_tree("job-1", "org-1")
        assert cancelled is not None
        assert cancelled.state == cancelled.stage == "cancelled"
        assert cancelled.cancellation_requested is True
        assert cancelled.completed_at is not None
        assert cancelled.lease_owner is None

        partitions = await ConnectorIngestionPartitionRepository(session).list_for_job(
            "job-1", "org-1"
        )
        batches = await ConnectorIngestionStageBatchRepository(session).list_for_job(
            "job-1", "org-1"
        )
        assert [row.state for row in partitions] == ["cancelled", "committed"]
        assert [row.state for row in batches] == ["cancelled", "committed"]
        assert partitions[0].lease_owner is None
        assert batches[0].writer_owner is None
        connection_state = await session.scalar(
            text("SELECT sync_state FROM connections WHERE number = 7")
        )
        assert connection_state == "cancelled"

        same = await repository.cancel_job_tree("job-1", "org-1")
        assert same is cancelled
        await session.commit()
    await engine.dispose()

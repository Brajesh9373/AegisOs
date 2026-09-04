"""Qualification tests for bounded, immutable partition extraction."""

from __future__ import annotations

import gzip
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from ecms.connectors.ingestion.coordinator import IngestionPlan
from ecms.connectors.ingestion.coordinator_runtime import (
    repository_workspace_path,
    store_manifest_plan,
)
from ecms.connectors.ingestion.extraction_runtime import (
    ExtractionHandler,
    PartitionWork,
)
from ecms.connectors.ingestion.manifest import ManifestSource, build_manifest
from ecms.connectors.ingestion.parallel_queue import ExtractionDelivery
from ecms.connectors.ingestion.partitioning import partition_manifest
from ecms.infrastructure.storage import InMemoryObjectStore


class FakeStore:
    def __init__(self, work: PartitionWork, *, register_result: bool = True) -> None:
        self.work = work
        self.register_result = register_result
        self.batches = []
        self.checkpoints = []
        self.is_staged = False

    async def load_claimed(self, delivery, worker_id):
        return self.work

    async def begin(self, work, worker_id):
        return None

    async def renew(self, work, worker_id):
        return True

    async def cancellation_requested(self, work):
        return False

    async def register_batch(self, work, batch, worker_id):
        self.batches.append(batch)
        return self.register_result

    async def checkpoint(self, work, **values):
        self.checkpoints.append(values)

    async def staged(self, work, worker_id):
        self.is_staged = True

    async def failed_attempt(self, work, worker_id, error):
        return None


class FakeGraphQueue:
    def __init__(self) -> None:
        self.messages = []

    async def enqueue(self, **identifiers):
        self.messages.append(identifiers)
        return str(len(self.messages))


def _repository(tmp_path: Path) -> tuple[Path, str]:
    git = shutil.which("git")
    assert git is not None
    repository = tmp_path / "repo"
    repository.mkdir()
    (repository / "a.py").write_text("print('a')\n", encoding="utf-8")
    (repository / "b.md").write_text("# B\n", encoding="utf-8")
    subprocess.run(  # noqa: S603
        [git, "init"], cwd=repository, check=True, capture_output=True
    )
    subprocess.run(  # noqa: S603
        [git, "add", "."], cwd=repository, check=True, capture_output=True
    )
    subprocess.run(  # noqa: S603
        [
            git,
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "-m",
            "fixture",
        ],
        cwd=repository,
        check=True,
        capture_output=True,
    )
    revision = subprocess.run(  # noqa: S603
        [git, "rev-parse", "HEAD"],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return repository, revision


@pytest.mark.asyncio
async def test_handler_stages_bounded_verified_batches(tmp_path: Path) -> None:
    repository, revision = _repository(tmp_path)
    sources = [
        ManifestSource("a.py", (repository / "a.py").read_bytes()),
        ManifestSource("b.md", (repository / "b.md").read_bytes()),
    ]
    manifest = build_manifest(sources)
    partition = partition_manifest(manifest, 1)[0]
    objects = InMemoryObjectStore()
    await store_manifest_plan(
        objects,
        object_key="manifests/m.jsonl.gz",
        revision=revision,
        plan=IngestionPlan(manifest, (partition,)),
    )
    work = PartitionWork(
        id="partition-1",
        job_id="job-1",
        organization_id="org-1",
        connection_id=7,
        manifest_id="manifest-1",
        manifest_object_key="manifests/m.jsonl.gz",
        manifest_checksum=manifest.checksum,
        resolved_revision=revision,
        partition_number=0,
        partition_count=1,
        partition_checksum=partition.checksum,
        repository=repository,
    )
    store = FakeStore(work)
    graph_queue = FakeGraphQueue()
    handler = ExtractionHandler(
        store=store,
        objects=objects,
        graph_queue=graph_queue,
        worker_id="worker-1",
        chunk_size=1,
        lease_poll_seconds=60,
    )

    await handler(ExtractionDelivery("1-0", "job-1", "manifest-1", "partition-1"))

    assert store.is_staged is True
    assert len(store.batches) == 2
    assert len(graph_queue.messages) == 2
    assert store.checkpoints[-1]["files_processed"] == 2
    for batch in store.batches:
        document = json.loads(gzip.decompress(batch.payload))
        canonical = json.dumps(
            document, ensure_ascii=False, separators=(",", ":"), sort_keys=True
        ).encode()
        assert hashlib.sha256(canonical).hexdigest() == batch.checksum
        assert document["edges"] == []
        assert len(document["nodes"]) == 1


@pytest.mark.asyncio
async def test_handler_rejects_file_changed_after_manifest(tmp_path: Path) -> None:
    repository, revision = _repository(tmp_path)
    original = (repository / "a.py").read_bytes()
    manifest = build_manifest([ManifestSource("a.py", original)])
    objects = InMemoryObjectStore()
    partition = partition_manifest(manifest, 1)[0]
    await store_manifest_plan(
        objects,
        object_key="manifest.jsonl.gz",
        revision=revision,
        plan=IngestionPlan(manifest, (partition,)),
    )
    (repository / "a.py").write_text("tampered", encoding="utf-8")
    work = PartitionWork(
        id="p",
        job_id="j",
        organization_id="o",
        connection_id=1,
        manifest_id="m",
        manifest_object_key="manifest.jsonl.gz",
        manifest_checksum=manifest.checksum,
        resolved_revision=revision,
        partition_number=0,
        partition_count=1,
        partition_checksum=None,
        repository=repository,
    )
    handler = ExtractionHandler(
        store=FakeStore(work),
        objects=objects,
        graph_queue=FakeGraphQueue(),
        worker_id="w",
    )

    with pytest.raises(ValueError, match=r"file (size|content) changed"):
        await handler(ExtractionDelivery("1-0", "j", "m", "p"))


@pytest.mark.asyncio
async def test_existing_durable_batch_is_republished_before_checkpoint(
    tmp_path: Path,
) -> None:
    repository, revision = _repository(tmp_path)
    content = (repository / "a.py").read_bytes()
    manifest = build_manifest([ManifestSource("a.py", content)])
    partition = partition_manifest(manifest, 1)[0]
    objects = InMemoryObjectStore()
    await store_manifest_plan(
        objects,
        object_key="manifest/recovery.jsonl.gz",
        revision=revision,
        plan=IngestionPlan(manifest, (partition,)),
    )
    work = PartitionWork(
        id="p-recovery",
        job_id="j-recovery",
        organization_id="o-recovery",
        connection_id=3,
        manifest_id="m-recovery",
        manifest_object_key="manifest/recovery.jsonl.gz",
        manifest_checksum=manifest.checksum,
        resolved_revision=revision,
        partition_number=0,
        partition_count=1,
        partition_checksum=partition.checksum,
        repository=repository,
    )
    store = FakeStore(work, register_result=False)
    queue = FakeGraphQueue()

    await ExtractionHandler(
        store=store,
        objects=objects,
        graph_queue=queue,
        worker_id="worker-recovery",
    )(ExtractionDelivery("1-0", work.job_id, work.manifest_id, work.id))

    assert len(queue.messages) == 1
    assert queue.messages[0]["stage_batch_id"] == store.batches[0].id
    assert store.checkpoints[-1]["files_processed"] == 1


def test_coordinator_and_extractor_share_opaque_workspace_path(tmp_path: Path) -> None:
    path = repository_workspace_path(tmp_path, "org/acme", "job/42")

    assert path.parent.parent == tmp_path
    assert "org" not in path.as_posix()
    assert "job" not in path.as_posix()
    assert path == repository_workspace_path(tmp_path, "org/acme", "job/42")


@pytest.mark.asyncio
async def test_encoded_ceiling_splits_deterministically_and_preserves_paths(
    tmp_path: Path,
) -> None:
    repository, revision = _repository(tmp_path)
    # Equal content deliberately proves path is part of stable node identity.
    content = ("x" * 700).encode()
    (repository / "a.py").write_bytes(content)
    (repository / "b.md").write_bytes(content)
    subprocess.run(  # noqa: ASYNC221,S603
        [shutil.which("git") or "git", "add", "."],
        cwd=repository,
        check=True,
        capture_output=True,
    )
    subprocess.run(  # noqa: ASYNC221,S603
        [
            shutil.which("git") or "git",
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "-m",
            "same-content",
        ],
        cwd=repository,
        check=True,
        capture_output=True,
    )
    revision = subprocess.run(  # noqa: ASYNC221,S603
        [shutil.which("git") or "git", "rev-parse", "HEAD"],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    manifest = build_manifest([ManifestSource("a.py", content), ManifestSource("b.md", content)])
    partition = partition_manifest(manifest, 1)[0]
    objects = InMemoryObjectStore()
    await store_manifest_plan(
        objects,
        object_key="manifest/same.jsonl.gz",
        revision=revision,
        plan=IngestionPlan(manifest, (partition,)),
    )
    work = PartitionWork(
        id="partition-same",
        job_id="job/same",
        organization_id="org/same",
        connection_id=99,
        manifest_id="manifest-same",
        manifest_object_key="manifest/same.jsonl.gz",
        manifest_checksum=manifest.checksum,
        resolved_revision=revision,
        partition_number=0,
        partition_count=1,
        partition_checksum=partition.checksum,
        repository=repository,
    )

    async def execute():
        store = FakeStore(work)
        handler = ExtractionHandler(
            store=store,
            objects=objects,
            graph_queue=FakeGraphQueue(),
            worker_id="worker",
            chunk_size=10,
            max_batch_encoded_bytes=1_500,
            lease_poll_seconds=60,
        )
        await handler(ExtractionDelivery("1-0", work.job_id, work.manifest_id, work.id))
        return store.batches

    first = await execute()
    second = await execute()

    assert len(first) == 2
    assert all(batch.encoded_byte_count <= 1_500 for batch in first)
    assert [(batch.id, batch.object_key) for batch in first] == [
        (batch.id, batch.object_key) for batch in second
    ]
    assert "org/same" not in first[0].object_key
    assert "job/same" not in first[0].object_key
    nodes = [json.loads(gzip.decompress(batch.payload))["nodes"][0]["id"] for batch in first]
    assert len(set(nodes)) == 2

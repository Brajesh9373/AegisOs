from __future__ import annotations

import gzip
import hashlib
import json
from dataclasses import replace

import pytest

from ecms.connectors.ingestion.graph_semaphore import GraphWriteLease
from ecms.connectors.ingestion.graph_writer_runtime import (
    GraphBatchHandler,
    GraphBatchWork,
    PublicationWork,
)
from ecms.connectors.ingestion.parallel_queue import GraphWriteDelivery
from ecms.connectors.ingestion.worker import ChunkWrite, GitJobSpec
from ecms.infrastructure.storage.object_store import InMemoryObjectStore


class FakeStore:
    def __init__(self, work: GraphBatchWork) -> None:
        self.work = work
        self.commits = 0
        self.retries = 0
        self.publication: PublicationWork | None = None
        self.publication_completes = 0

    async def claim(self, _delivery, _writer_id):
        return self.work

    async def renew(self, _work, _writer_id):
        return True

    async def cancellation_requested(self, _work):
        return False

    async def commit(self, _work, _writer_id):
        self.commits += 1

    async def retry(self, _work, _writer_id, _error):
        self.retries += 1

    async def reconcile(self, _work, _writer_id):
        return self.publication

    async def publication_complete(self, _publication, _writer_id):
        self.publication_completes += 1

    async def publication_failed(self, _publication, _writer_id, _error):
        pass

    async def exhausted(self, _delivery, _error):
        pass


class FakeSemaphore:
    def __init__(self) -> None:
        self.acquired = 0
        self.released = 0

    async def acquire(self):
        self.acquired += 1
        return GraphWriteLease("lease")

    async def renew(self, _lease):
        return True

    async def release(self, _lease):
        self.released += 1
        return True


class CapturingLegacySink:
    def __init__(self) -> None:
        self.files = []
        self.finalized = []

    async def write(self, _spec, files):
        self.files.extend(files)
        return ChunkWrite(nodes=len(files))

    async def finalize_persisted(self, spec, *, success_count):
        self.finalized.append((spec.job_id, success_count))


def _document(*, edges=None):
    return {
        "schema_version": 1,
        "job_id": "job-1",
        "manifest_id": "manifest-1",
        "partition_id": "partition-1",
        "sequence_number": 0,
        "nodes": [
            {
                "id": "node-1",
                "labels": ["UKO", "File"],
                "properties": {
                    "organization_id": "org-1",
                    "ingestion_revision": "abc123",
                    "path": "src/app.py",
                    "name": "src/app.py",
                    "source": "git",
                    "extractor_type": "python",
                    "size_bytes": 6,
                    "content": "x = 1\n",
                },
            }
        ],
        "edges": edges or [],
    }


def _payload(document):
    canonical = json.dumps(
        document, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode()
    return canonical, gzip.compress(canonical, mtime=0)


def _work(canonical: bytes, payload: bytes, *, edge_count: int = 0):
    return GraphBatchWork(
        batch_id="batch-1",
        partition_id="partition-1",
        manifest_id="manifest-1",
        job_id="job-1",
        organization_id="org-1",
        object_key="staged/batch.json.gz",
        checksum=hashlib.sha256(canonical).hexdigest(),
        byte_count=len(payload),
        node_count=1,
        edge_count=edge_count,
        sequence_number=0,
        spec=GitJobSpec(
            job_id="job-1",
            organization_id="org-1",
            repo_url="https://example.test/repo.git",
            branch="main",
            connection_id=7,
            resolved_revision="abc123",
        ),
    )


async def test_staged_file_is_replayed_through_current_legacy_semantics() -> None:
    canonical, payload = _payload(_document())
    work = _work(canonical, payload)
    store = FakeStore(work)
    objects = InMemoryObjectStore()
    await objects.put_object(work.object_key, payload)
    sink = CapturingLegacySink()
    semaphore = FakeSemaphore()
    handler = GraphBatchHandler(
        store=store,
        objects=objects,
        semaphore=semaphore,  # type: ignore[arg-type]
        sink=sink,  # type: ignore[arg-type]
        writer_id="writer-1",
    )

    await handler(
        GraphWriteDelivery("1-0", "job-1", "partition-1", "batch-1")
    )

    assert [(item.relative_path, item.content, item.size_bytes) for item in sink.files] == [
        ("src/app.py", "x = 1\n", 6)
    ]
    assert store.commits == 1
    assert semaphore.acquired == semaphore.released == 1


async def test_writer_fails_closed_on_checksum_or_unproven_edge_semantics() -> None:
    canonical, payload = _payload(_document())
    work = _work(canonical, payload)
    objects = InMemoryObjectStore()
    await objects.put_object(work.object_key, payload)
    store = FakeStore(replace(work, checksum="0" * 64))
    handler = GraphBatchHandler(
        store=store,
        objects=objects,
        semaphore=FakeSemaphore(),  # type: ignore[arg-type]
        sink=CapturingLegacySink(),  # type: ignore[arg-type]
        writer_id="writer-1",
    )
    delivery = GraphWriteDelivery("1-0", "job-1", "partition-1", "batch-1")
    with pytest.raises(ValueError, match="checksum"):
        await handler(delivery)
    assert store.retries == 1

    document = _document(
        edges=[{"source": "node-1", "target": "node-2", "type": "DEPENDS_ON"}]
    )
    edge_canonical, edge_payload = _payload(document)
    edge_work = _work(edge_canonical, edge_payload, edge_count=1)
    await objects.put_object(edge_work.object_key, edge_payload)
    edge_store = FakeStore(edge_work)
    edge_handler = GraphBatchHandler(
        store=edge_store,
        objects=objects,
        semaphore=FakeSemaphore(),  # type: ignore[arg-type]
        sink=CapturingLegacySink(),  # type: ignore[arg-type]
        writer_id="writer-1",
    )
    with pytest.raises(ValueError, match="not yet proven equivalent"):
        await edge_handler(delivery)


async def test_committed_redelivery_only_reconciles_and_finalizes_once() -> None:
    canonical, payload = _payload(_document())
    work = replace(_work(canonical, payload), already_committed=True)
    store = FakeStore(work)
    store.publication = PublicationWork(work.spec, success_count=12)
    sink = CapturingLegacySink()
    handler = GraphBatchHandler(
        store=store,
        objects=InMemoryObjectStore(),
        semaphore=FakeSemaphore(),  # type: ignore[arg-type]
        sink=sink,  # type: ignore[arg-type]
        writer_id="writer-1",
    )

    await handler(
        GraphWriteDelivery("1-0", "job-1", "partition-1", "batch-1")
    )

    assert store.commits == 0
    assert sink.finalized == [("job-1", 12)]
    assert store.publication_completes == 1

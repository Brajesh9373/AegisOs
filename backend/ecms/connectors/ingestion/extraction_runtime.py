"""Persistence-aware runtime for partitioned connector extraction.

The extractor is intentionally graph-database blind.  It validates its immutable
manifest slice, produces bounded canonical batches in object storage, persists batch
metadata, and publishes identifiers for the separately bounded graph writer.
"""

from __future__ import annotations

import asyncio
import gzip
import hashlib
import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, cast

from ecms.connectors.ingestion.coordinator_runtime import iter_stored_manifest
from ecms.connectors.ingestion.manifest import ManifestEntry
from ecms.connectors.ingestion.parallel_queue import ExtractionDelivery, GraphWriteQueue
from ecms.infrastructure.storage.object_store import ObjectStore


class ExtractionCancelledError(RuntimeError):
    """Raised when durable cancellation or lease loss stops extraction."""


@dataclass(frozen=True, slots=True)
class PartitionWork:
    """All durable identifiers needed to process one claimed partition."""

    id: str
    job_id: str
    organization_id: str
    connection_id: int
    manifest_id: str
    manifest_object_key: str
    manifest_checksum: str
    resolved_revision: str
    partition_number: int
    partition_count: int
    partition_checksum: str | None
    repository: Path
    next_sequence: int = 0
    files_processed: int = 0
    nodes_extracted: int = 0
    edges_extracted: int = 0


@dataclass(frozen=True, slots=True)
class StagedBatch:
    """Checksummed immutable graph payload ready for durable registration."""

    id: str
    sequence_number: int
    object_key: str
    checksum: str
    payload: bytes
    node_count: int
    edge_count: int
    file_count: int
    encoded_byte_count: int


@dataclass(frozen=True, slots=True)
class LoadedPartition:
    """Validated entries selected from a streamed coordinator manifest."""

    entries: tuple[ManifestEntry, ...]
    checksum: str


class ExtractionStore(Protocol):
    """Short-transaction persistence boundary used by the runtime."""

    async def load_claimed(  # noqa: D102
        self, delivery: ExtractionDelivery, worker_id: str
    ) -> PartitionWork | None: ...

    async def begin(self, work: PartitionWork, worker_id: str) -> None: ...  # noqa: D102
    async def renew(self, work: PartitionWork, worker_id: str) -> bool: ...  # noqa: D102
    async def cancellation_requested(self, work: PartitionWork) -> bool: ...  # noqa: D102
    async def register_batch(  # noqa: D102
        self, work: PartitionWork, batch: StagedBatch, worker_id: str
    ) -> bool: ...
    async def checkpoint(  # noqa: D102
        self,
        work: PartitionWork,
        *,
        files_processed: int,
        nodes_extracted: int,
        edges_extracted: int,
        next_sequence: int,
        worker_id: str,
    ) -> None: ...
    async def staged(self, work: PartitionWork, worker_id: str) -> None: ...  # noqa: D102
    async def failed_attempt(  # noqa: D102
        self, work: PartitionWork, worker_id: str, error: Exception
    ) -> None: ...


class ExtractionHandler:
    """Validate, extract, and durably stage one disjoint manifest partition."""

    def __init__(
        self,
        *,
        store: ExtractionStore,
        objects: ObjectStore,
        graph_queue: GraphWriteQueue,
        worker_id: str,
        chunk_size: int = 25,
        max_batch_encoded_bytes: int = 4 * 1024 * 1024,
        lease_poll_seconds: float = 2,
    ) -> None:
        """Configure durable boundaries and bounded extraction policy."""
        if chunk_size < 1:
            raise ValueError("chunk_size must be positive")
        if max_batch_encoded_bytes < 1:
            raise ValueError("max_batch_encoded_bytes must be positive")
        self._store = store
        self._objects = objects
        self._graph_queue = graph_queue
        self._worker_id = worker_id
        self._chunk_size = chunk_size
        self._max_batch_encoded_bytes = max_batch_encoded_bytes
        self._lease_poll_seconds = lease_poll_seconds

    async def __call__(self, delivery: ExtractionDelivery) -> None:
        """Process a claimed delivery; acknowledge is owned by ``ExtractionWorker``."""
        work = await self._store.load_claimed(delivery, self._worker_id)
        if work is None:
            return
        try:
            await self._store.begin(work, self._worker_id)
            partition = await _load_partition(self._objects, work)
            if work.partition_checksum and partition.checksum != work.partition_checksum:
                raise ValueError("partition checksum does not match immutable manifest")
            await _validate_revision(work.repository, work.resolved_revision)
        except Exception as exc:
            await self._store.failed_attempt(work, self._worker_id, exc)
            raise

        stop = asyncio.Event()
        lease_task = asyncio.create_task(self._guard_lease(work, stop))
        processed = work.files_processed
        nodes = work.nodes_extracted
        edges = work.edges_extracted
        sequence = work.next_sequence
        try:
            remaining = partition.entries[processed:]
            pending: list[dict[str, object]] = []
            pending_files = 0
            for entry in remaining:
                if stop.is_set():
                    raise ExtractionCancelledError("partition lease lost or cancelled")
                record = (await asyncio.to_thread(_extract_entries, work, (entry,)))[0]
                candidate = _build_batch(
                    work, sequence, (*pending, record), pending_files + 1
                )
                if candidate.encoded_byte_count > self._max_batch_encoded_bytes:
                    if not pending:
                        raise ValueError(
                            f"derived record exceeds staged batch byte limit: "
                            f"{entry.relative_path}"
                        )
                    batch = _build_batch(work, sequence, pending, pending_files)
                    processed, nodes, edges, sequence = await self._stage(
                        work,
                        batch,
                        processed=processed,
                        nodes=nodes,
                        edges=edges,
                        sequence=sequence,
                    )
                    pending = [record]
                    pending_files = 1
                    candidate = _build_batch(work, sequence, pending, pending_files)
                    if candidate.encoded_byte_count > self._max_batch_encoded_bytes:
                        raise ValueError(
                            f"derived record exceeds staged batch byte limit: "
                            f"{entry.relative_path}"
                        )
                else:
                    pending.append(record)
                    pending_files += 1
                if pending_files < self._chunk_size:
                    continue
                batch = _build_batch(work, sequence, pending, pending_files)
                processed, nodes, edges, sequence = await self._stage(
                    work,
                    batch,
                    processed=processed,
                    nodes=nodes,
                    edges=edges,
                    sequence=sequence,
                )
                pending = []
                pending_files = 0
            if pending:
                batch = _build_batch(work, sequence, pending, pending_files)
                processed, nodes, edges, sequence = await self._stage(
                    work,
                    batch,
                    processed=processed,
                    nodes=nodes,
                    edges=edges,
                    sequence=sequence,
                )
            await self._store.staged(work, self._worker_id)
        except Exception as exc:
            await self._store.failed_attempt(work, self._worker_id, exc)
            raise
        finally:
            stop.set()
            lease_task.cancel()
            await asyncio.gather(lease_task, return_exceptions=True)

    async def _stage(
        self,
        work: PartitionWork,
        batch: StagedBatch,
        *,
        processed: int,
        nodes: int,
        edges: int,
        sequence: int,
    ) -> tuple[int, int, int, int]:
        """Make one object and checkpoint durable before advancing."""
        await self._objects.put_object(batch.object_key, batch.payload)
        await self._store.register_batch(work, batch, self._worker_id)
        # Republish on idempotent recovery too: a crash after the metadata
        # commit but before XADD must not strand a durable batch.
        await self._graph_queue.enqueue(
            job_id=work.job_id,
            partition_id=work.id,
            stage_batch_id=batch.id,
        )
        processed += batch.file_count
        nodes += batch.node_count
        edges += batch.edge_count
        sequence += 1
        await self._store.checkpoint(
            work,
            files_processed=processed,
            nodes_extracted=nodes,
            edges_extracted=edges,
            next_sequence=sequence,
            worker_id=self._worker_id,
        )
        return processed, nodes, edges, sequence

    async def _guard_lease(self, work: PartitionWork, stop: asyncio.Event) -> None:
        while not stop.is_set():
            await asyncio.sleep(self._lease_poll_seconds)
            if (
                not await self._store.renew(work, self._worker_id)
                or await self._store.cancellation_requested(work)
            ):
                stop.set()
                return


async def _load_partition(
    objects: ObjectStore, work: PartitionWork
) -> LoadedPartition:
    selected: list[ManifestEntry] = []
    digest = hashlib.sha256()
    digest.update(b"[")
    seen = 0
    total_bytes = 0
    header: dict[str, object] | None = None
    async for record in iter_stored_manifest(objects, work.manifest_object_key):
        if header is None:
            header = record
            if (
                record.get("revision") != work.resolved_revision
                or record.get("manifest_checksum") != work.manifest_checksum
                or _as_int(record.get("partition_count", 0)) != work.partition_count
            ):
                raise ValueError("manifest header differs from durable record")
            continue
        entry = ManifestEntry(
            relative_path=str(record["relative_path"]),
            size_bytes=_as_int(record["size_bytes"]),
            content_hash=str(record["content_hash"]),
            extractor_type=str(record["extractor_type"]),
        )
        if record.get("entry_checksum") != entry.checksum:
            raise ValueError("stored manifest entry checksum is invalid")
        partition_index = _as_int(record["partition_index"])
        if not 0 <= partition_index < work.partition_count:
            raise ValueError("stored manifest partition index is invalid")
        if seen:
            digest.update(b",")
        digest.update(
            json.dumps(
                entry.as_dict(),
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        )
        seen += 1
        total_bytes += entry.size_bytes
        if partition_index == work.partition_number:
            selected.append(entry)
    digest.update(b"]")
    if header is None:
        raise ValueError("stored manifest has no header")
    if seen != _as_int(header["file_count"]) or total_bytes != _as_int(
        header["total_bytes"]
    ):
        raise ValueError("stored manifest totals are invalid")
    if digest.hexdigest() != work.manifest_checksum:
        raise ValueError("stored manifest content checksum is invalid")
    checksum_payload = {
        "manifest_checksum": work.manifest_checksum,
        "partition_index": work.partition_number,
        "entries": [entry.checksum for entry in selected],
        "total_weight": sum(max(1, entry.size_bytes) for entry in selected),
    }
    partition_checksum = hashlib.sha256(
        json.dumps(
            checksum_payload, sort_keys=True, separators=(",", ":")
        ).encode()
    ).hexdigest()
    return LoadedPartition(tuple(selected), partition_checksum)


def _as_int(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int | str):
        raise ValueError("stored manifest integer field is invalid")
    return int(value)


async def _validate_revision(repository: Path, expected: str) -> None:
    is_safe = await asyncio.to_thread(
        lambda: repository.is_dir() and not repository.is_symlink()
    )
    if not is_safe:
        raise ValueError("repository workspace is unavailable or unsafe")
    process = await asyncio.create_subprocess_exec(
        "git",
        "-C",
        str(repository),
        "rev-parse",
        "HEAD",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
    )
    stdout, _ = await process.communicate()
    actual = stdout.decode().strip()
    if process.returncode or actual != expected:
        raise ValueError("repository revision differs from immutable manifest")


def _extract_entries(
    work: PartitionWork, entries: Sequence[ManifestEntry]
) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    root = work.repository.resolve(strict=True)
    for entry in entries:
        unresolved = root / entry.relative_path
        if unresolved.is_symlink():
            raise ValueError(f"manifest path is a symlink: {entry.relative_path}")
        path = unresolved.resolve(strict=True)
        if root not in path.parents or not path.is_file():
            raise ValueError(f"manifest path escaped repository: {entry.relative_path}")
        content = path.read_bytes()
        if len(content) != entry.size_bytes:
            raise ValueError(f"file size changed: {entry.relative_path}")
        if hashlib.sha256(content).hexdigest() != entry.content_hash:
            raise ValueError(f"file content changed: {entry.relative_path}")
        identity = (
            f"{work.organization_id}\0{work.connection_id}\0{entry.relative_path}"
        )
        node_id = f"git:file:{hashlib.sha256(identity.encode()).hexdigest()}"
        records.append(
            {
                "nodes": [
                    {
                        "id": node_id,
                        "labels": ["UKO", "File"],
                        "properties": {
                            "organization_id": work.organization_id,
                            "ingestion_revision": work.resolved_revision,
                            "path": entry.relative_path,
                            "name": entry.relative_path,
                            "source": "git",
                            "extractor_type": entry.extractor_type,
                            "size_bytes": entry.size_bytes,
                            "content": content.decode("utf-8", errors="replace"),
                        },
                    }
                ],
                "edges": [],
            }
        )
    return records


def _build_batch(
    work: PartitionWork,
    sequence: int,
    records: Sequence[dict[str, object]],
    file_count: int,
) -> StagedBatch:
    nodes = [
        node
        for record in records
        for node in cast(list[dict[str, Any]], record["nodes"])
    ]
    edges = [
        edge
        for record in records
        for edge in cast(list[dict[str, Any]], record["edges"])
    ]
    document = {
        "schema_version": 1,
        "job_id": work.job_id,
        "manifest_id": work.manifest_id,
        "partition_id": work.id,
        "sequence_number": sequence,
        "nodes": nodes,
        "edges": edges,
    }
    canonical = json.dumps(
        document, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode()
    checksum = hashlib.sha256(canonical).hexdigest()
    payload = gzip.compress(canonical, mtime=0)
    batch_id = hashlib.sha256(
        f"{work.id}:{sequence}:{checksum}".encode()
    ).hexdigest()
    tenant = hashlib.sha256(work.organization_id.encode()).hexdigest()[:20]
    job = hashlib.sha256(work.job_id.encode()).hexdigest()[:20]
    return StagedBatch(
        id=batch_id,
        sequence_number=sequence,
        object_key=(
            f"connector-ingestion/staged/{tenant}/{job}/"
            f"{work.id}/{sequence:08d}-{checksum}.json.gz"
        ),
        checksum=checksum,
        payload=payload,
        node_count=len(nodes),
        edge_count=len(edges),
        file_count=file_count,
        encoded_byte_count=len(canonical),
    )

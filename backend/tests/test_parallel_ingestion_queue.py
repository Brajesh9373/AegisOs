from __future__ import annotations

import fakeredis.aioredis

from ecms.connectors.ingestion.extraction_worker import ExtractionWorker
from ecms.connectors.ingestion.parallel_queue import (
    EXTRACTION_GROUP,
    EXTRACTION_STREAM,
    GRAPH_WRITE_GROUP,
    GRAPH_WRITE_STREAM,
    DeliveryOutcome,
    ExtractionQueue,
    GraphWriteQueue,
)


async def test_streams_are_separate_and_contain_ids_only() -> None:
    redis = fakeredis.aioredis.FakeRedis()
    extraction = ExtractionQueue(redis, consumer="extractor-1")
    graph = GraphWriteQueue(redis, consumer="writer-1")
    await extraction.ensure_group()
    await graph.ensure_group()

    await extraction.enqueue(job_id="job-1", manifest_id="manifest-1", partition_id="p-1")
    await graph.enqueue(job_id="job-1", partition_id="p-1", stage_batch_id="batch-1")

    extraction_fields = (await redis.xrange(EXTRACTION_STREAM))[0][1]
    graph_fields = (await redis.xrange(GRAPH_WRITE_STREAM))[0][1]
    assert set(extraction_fields) == {b"job_id", b"manifest_id", b"partition_id"}
    assert set(graph_fields) == {b"job_id", b"partition_id", b"stage_batch_id"}
    assert EXTRACTION_STREAM != GRAPH_WRITE_STREAM
    assert EXTRACTION_GROUP != GRAPH_WRITE_GROUP


async def test_stale_delivery_can_be_claimed_and_acknowledged() -> None:
    redis = fakeredis.aioredis.FakeRedis()
    first = ExtractionQueue(redis, consumer="extractor-dead")
    second = ExtractionQueue(redis, consumer="extractor-live")
    await first.ensure_group()
    await first.enqueue(job_id="job-1", manifest_id="manifest-1", partition_id="p-1")
    abandoned = await first.read(block_ms=1)
    assert abandoned is not None

    reclaimed = await second.claim_stale(min_idle_ms=0)
    assert reclaimed is not None
    assert reclaimed.message_id == abandoned.message_id
    assert reclaimed.partition_id == "p-1"

    await second.acknowledge(reclaimed)
    assert (await redis.xpending(EXTRACTION_STREAM, EXTRACTION_GROUP))["pending"] == 0


async def test_retry_leaves_pending_then_exhaustion_acknowledges() -> None:
    redis = fakeredis.aioredis.FakeRedis()
    queue = GraphWriteQueue(redis, consumer="writer-1")
    await queue.ensure_group()
    await queue.enqueue(job_id="job-1", partition_id="p-1", stage_batch_id="batch-1")
    delivery = await queue.read(block_ms=1)
    assert delivery is not None

    assert await queue.retry_or_exhaust(delivery, max_deliveries=2) is DeliveryOutcome.RETRY
    assert (await redis.xpending(GRAPH_WRITE_STREAM, GRAPH_WRITE_GROUP))["pending"] == 1
    assert await queue.retry_or_exhaust(delivery, max_deliveries=2) is DeliveryOutcome.EXHAUSTED
    assert (await redis.xpending(GRAPH_WRITE_STREAM, GRAPH_WRITE_GROUP))["pending"] == 0


async def test_extraction_worker_retries_then_reports_exhaustion() -> None:
    redis = fakeredis.aioredis.FakeRedis()
    queue = ExtractionQueue(redis, consumer="extractor-1")
    await queue.ensure_group()
    await queue.enqueue(job_id="job-1", manifest_id="manifest-1", partition_id="p-1")
    exhausted: list[tuple[str, str]] = []

    async def fail(delivery):
        raise RuntimeError(f"failed {delivery.partition_id}")

    async def record(delivery, exc):
        exhausted.append((delivery.partition_id, str(exc)))

    worker = ExtractionWorker(
        queue,
        fail,
        max_deliveries=2,
        stale_after_ms=0,
        on_exhausted=record,
    )
    first = await worker.process_one(block_ms=1)
    second = await worker.process_one(block_ms=1)

    assert first.outcome is DeliveryOutcome.RETRY
    assert second.outcome is DeliveryOutcome.EXHAUSTED
    assert exhausted == [("p-1", "failed p-1")]


async def test_extraction_worker_acknowledges_success() -> None:
    redis = fakeredis.aioredis.FakeRedis()
    queue = ExtractionQueue(redis, consumer="extractor-1")
    await queue.ensure_group()
    await queue.enqueue(job_id="job-1", manifest_id="manifest-1", partition_id="p-1")
    seen: list[str] = []

    async def handle(delivery):
        seen.append(delivery.partition_id)

    result = await ExtractionWorker(queue, handle, stale_after_ms=0).process_one(block_ms=1)

    assert result.processed
    assert result.outcome is None
    assert seen == ["p-1"]
    assert (await redis.xpending(EXTRACTION_STREAM, EXTRACTION_GROUP))["pending"] == 0


async def test_exhausted_delivery_stays_pending_when_terminal_persistence_fails() -> None:
    redis = fakeredis.aioredis.FakeRedis()
    queue = ExtractionQueue(redis, consumer="extractor-1")
    await queue.ensure_group()
    await queue.enqueue(job_id="job-1", manifest_id="manifest-1", partition_id="p-1")

    async def fail(_delivery):
        raise RuntimeError("extract failed")

    async def persistence_fails(_delivery, _exc):
        raise RuntimeError("database unavailable")

    worker = ExtractionWorker(
        queue,
        fail,
        max_deliveries=1,
        stale_after_ms=0,
        on_exhausted=persistence_fails,
    )

    try:
        await worker.process_one(block_ms=1)
    except RuntimeError as exc:
        assert str(exc) == "database unavailable"
    else:
        raise AssertionError("terminal persistence failure must escape")

    assert (await redis.xpending(EXTRACTION_STREAM, EXTRACTION_GROUP))["pending"] == 1

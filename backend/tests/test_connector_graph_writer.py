from __future__ import annotations

import fakeredis.aioredis
import pytest

from ecms.connectors.ingestion.fan_in import reconcile_fan_in
from ecms.connectors.ingestion.graph_writer import GraphWriter
from ecms.connectors.ingestion.parallel_queue import (
    GRAPH_WRITE_GROUP,
    GRAPH_WRITE_STREAM,
    DeliveryOutcome,
    GraphWriteQueue,
)


async def test_graph_writer_acknowledges_only_after_handler_success() -> None:
    redis = fakeredis.aioredis.FakeRedis()
    queue = GraphWriteQueue(redis, consumer="writer-1")
    await queue.ensure_group()
    await queue.enqueue(job_id="job", partition_id="part", stage_batch_id="batch")
    seen: list[str] = []

    async def handle(delivery) -> None:
        seen.append(delivery.stage_batch_id)

    result = await GraphWriter(queue, handle, stale_after_ms=0).process_one(block_ms=1)

    assert result.processed
    assert result.outcome is None
    assert seen == ["batch"]
    assert (await redis.xpending(GRAPH_WRITE_STREAM, GRAPH_WRITE_GROUP))["pending"] == 0


async def test_graph_writer_exhaustion_is_observable() -> None:
    redis = fakeredis.aioredis.FakeRedis()
    queue = GraphWriteQueue(redis, consumer="writer-1")
    await queue.ensure_group()
    await queue.enqueue(job_id="job", partition_id="part", stage_batch_id="batch")
    exhausted: list[str] = []

    async def fail(_delivery) -> None:
        raise RuntimeError("write failed")

    async def record(delivery, _exc) -> None:
        exhausted.append(delivery.stage_batch_id)

    writer = GraphWriter(
        queue,
        fail,
        max_deliveries=1,
        stale_after_ms=0,
        on_exhausted=record,
    )
    result = await writer.process_one(block_ms=1)

    assert result.outcome is DeliveryOutcome.EXHAUSTED
    assert exhausted == ["batch"]


async def test_graph_writer_does_not_ack_if_durable_exhaustion_callback_fails() -> None:
    redis = fakeredis.aioredis.FakeRedis()
    queue = GraphWriteQueue(redis, consumer="writer-1")
    await queue.ensure_group()
    await queue.enqueue(job_id="job", partition_id="part", stage_batch_id="batch")

    async def fail(_delivery) -> None:
        raise RuntimeError("write failed")

    async def persistence_down(_delivery, _exc) -> None:
        raise RuntimeError("database unavailable")

    writer = GraphWriter(
        queue,
        fail,
        max_deliveries=1,
        stale_after_ms=0,
        on_exhausted=persistence_down,
    )
    with pytest.raises(RuntimeError, match="database unavailable"):
        await writer.process_one(block_ms=1)

    assert (await redis.xpending(GRAPH_WRITE_STREAM, GRAPH_WRITE_GROUP))["pending"] == 1


def test_fan_in_waits_for_all_commits() -> None:
    waiting = reconcile_fan_in(
        partition_states={"committed": 3, "staged": 1},
        batch_states={"committed": 8},
        expected_partitions=4,
    )
    assert not waiting.ready_to_publish
    assert not waiting.terminal_failure

    ready = reconcile_fan_in(
        partition_states={"committed": 4},
        batch_states={"committed": 8},
        expected_partitions=4,
    )
    assert ready.ready_to_publish


def test_fan_in_rejects_missing_or_failed_children() -> None:
    mismatch = reconcile_fan_in(
        partition_states={"committed": 3},
        batch_states={"committed": 8},
        expected_partitions=4,
    )
    assert mismatch.terminal_failure

    failed = reconcile_fan_in(
        partition_states={"committed": 3, "failed": 1},
        batch_states={"committed": 8},
        expected_partitions=4,
    )
    assert failed.terminal_failure

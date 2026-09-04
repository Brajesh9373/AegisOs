from __future__ import annotations

import fakeredis.aioredis

from ecms.connectors.ingestion.queue import GROUP, STREAM, IngestionQueue


async def test_queue_payload_contains_identifiers_only() -> None:
    redis = fakeredis.aioredis.FakeRedis()
    queue = IngestionQueue(redis, consumer="worker-1")
    await queue.ensure_group()

    await queue.enqueue("job-1", "org-1")
    job = await queue.read(block_ms=1)

    assert job is not None
    assert job.job_id == "job-1"
    assert job.organization_id == "org-1"
    entries = await redis.xrange(STREAM)
    fields = entries[0][1]
    assert set(fields) == {b"job_id", b"organization_id", b"requested_at"}
    assert await redis.xpending(STREAM, GROUP)

    await queue.acknowledge(job)
    assert (await redis.xpending(STREAM, GROUP))["pending"] == 0

from __future__ import annotations

import fakeredis.aioredis

from ecms.api.rest import connector_ingestions
from ecms.configuration.schemas.settings import AppSettings


async def test_parallel_readiness_requires_declared_worker_capacity(
    monkeypatch,
) -> None:
    redis = fakeredis.aioredis.FakeRedis()
    settings = AppSettings(
        connector_parallel_ingestion_enabled=True,
        connector_extraction_worker_count=2,
    )
    monkeypatch.setattr(connector_ingestions, "get_settings", lambda: settings)
    monkeypatch.setattr(
        connector_ingestions.Redis,
        "from_url",
        lambda *_args, **_kwargs: redis,
    )
    await redis.set("ecms:connector-ingestion:coordinator-health:c1", "1", ex=30)
    await redis.set("ecms:connector-ingestion:extractor-health:e1", "1", ex=30)
    await redis.set("ecms:connector-ingestion:graph-writer-health:w1", "1", ex=30)

    assert not await connector_ingestions._parallel_workers_ready()

    await redis.set("ecms:connector-ingestion:extractor-health:e2", "1", ex=30)
    assert await connector_ingestions._parallel_workers_ready()

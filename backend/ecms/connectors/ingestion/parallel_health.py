"""Role-aware liveness probe for parallel connector worker containers."""

from __future__ import annotations

import asyncio
import os
import socket

from redis.asyncio import Redis

from ecms.configuration.schemas.settings import get_settings

_PREFIXES = {
    "legacy": "ecms:connector-ingestion:worker-health:",
    "coordinator": "ecms:connector-ingestion:coordinator-health:",
    "extractor": "ecms:connector-ingestion:extractor-health:",
    "graph-writer": "ecms:connector-ingestion:graph-writer-health:",
}


async def check(role: str) -> bool:
    """Return whether this container owns a current heartbeat for ``role``."""
    prefix = _PREFIXES.get(role)
    if prefix is None:
        return False
    redis = Redis.from_url(get_settings().redis_url, socket_connect_timeout=2, socket_timeout=2)
    try:
        pattern = f"{prefix}{socket.gethostname()}-*"
        async for _key in redis.scan_iter(match=pattern, count=20):
            return True
        return False
    finally:
        await redis.aclose()


def main() -> None:
    """Exit non-zero for an invalid role or absent heartbeat."""
    try:
        role = os.environ.get("ECMS_CONNECTOR_WORKER_ROLE", "")
        if role == "parent":
            role = (
                "coordinator" if get_settings().connector_parallel_ingestion_enabled else "legacy"
            )
        healthy = asyncio.run(check(role))
    except Exception:
        healthy = False
    raise SystemExit(0 if healthy else 1)


if __name__ == "__main__":
    main()

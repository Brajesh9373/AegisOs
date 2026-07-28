"""Health probe for a connector-ingestion worker container."""

from __future__ import annotations

import asyncio
import socket

from redis.asyncio import Redis

from ecms.configuration.schemas.settings import get_settings
from ecms.connectors.ingestion.queue import HEALTH_PREFIX


async def check() -> bool:
    """Return whether this container owns a current heartbeat."""
    redis = Redis.from_url(
        get_settings().redis_url,
        socket_connect_timeout=2,
        socket_timeout=2,
    )
    try:
        return bool(await redis.keys(f"{HEALTH_PREFIX}{socket.gethostname()}-*"))
    finally:
        await redis.aclose()


def main() -> None:
    """Exit non-zero when worker liveness is absent."""
    try:
        healthy = asyncio.run(check())
    except Exception:
        healthy = False
    raise SystemExit(0 if healthy else 1)


if __name__ == "__main__":
    main()

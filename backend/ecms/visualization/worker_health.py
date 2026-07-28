"""Container health probe for the dedicated knowledge-graph snapshot worker."""

from __future__ import annotations

import asyncio
import socket

from redis.asyncio import Redis

from ecms.configuration.schemas.settings import get_settings
from ecms.visualization.snapshot_queue import HEALTH_PREFIX


async def check() -> bool:
    """Return whether this container owns a current worker heartbeat."""
    redis = Redis.from_url(
        get_settings().redis_url,
        socket_connect_timeout=2,
        socket_timeout=2,
    )
    try:
        keys = await redis.keys(f"{HEALTH_PREFIX}{socket.gethostname()}-*")
        return bool(keys)
    finally:
        await redis.aclose()


def main() -> None:
    """Exit non-zero when the worker heartbeat is absent or Redis is unavailable."""
    try:
        healthy = asyncio.run(check())
    except Exception:
        healthy = False
    raise SystemExit(0 if healthy else 1)


if __name__ == "__main__":
    main()

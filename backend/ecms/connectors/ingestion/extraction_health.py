"""Container health probe for a parallel extraction worker."""

from __future__ import annotations

import asyncio
import socket

from redis.asyncio import Redis

from ecms.configuration.schemas.settings import get_settings


async def check() -> bool:
    """Return whether a process in this container has a current heartbeat."""
    redis = Redis.from_url(
        get_settings().redis_url, socket_connect_timeout=2, socket_timeout=2
    )
    try:
        keys = await redis.keys(
            f"ecms:connector-ingestion:extractor-health:{socket.gethostname()}-*"
        )
        return bool(keys)
    finally:
        await redis.aclose()


def main() -> None:
    """Exit non-zero when no extraction heartbeat exists."""
    try:
        healthy = asyncio.run(check())
    except Exception:
        healthy = False
    raise SystemExit(0 if healthy else 1)


if __name__ == "__main__":
    main()

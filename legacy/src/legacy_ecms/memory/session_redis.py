"""Redis-backed SessionMemory — shared across processes.

Drop-in replacement for the in-process SessionMemory (session.py).
Same interface: set/get/snapshot. Backed by Redis with TTL expiry.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

logger = logging.getLogger(__name__)


class RedisSessionMemory:
    """TTL-backed session memory using Redis.

    Uses the same interface as SessionMemory so it's a drop-in replacement.
    Keys are prefixed with ecms:session:{workspace_id}: for tenant isolation.
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6380/0",
        default_ttl_seconds: int = 3600,
        workspace_id: str = "default",
    ) -> None:
        self.default_ttl_seconds = default_ttl_seconds
        self._workspace_id = workspace_id
        self._pool: Any = None
        try:
            import redis
            self._pool = redis.ConnectionPool.from_url(
                redis_url,
                decode_responses=True,
                max_connections=20,
            )
            self._available = True
        except Exception as exc:
            logger.warning("Redis unavailable, session memory will be empty: %s", exc)
            self._available = False

    def _key(self, session_id: str, key: str) -> str:
        return f"ecms:session:{self._workspace_id}:{session_id}:{key}"

    def _pattern(self, session_id: str) -> str:
        return f"ecms:session:{self._workspace_id}:{session_id}:*"

    def _prefix(self, session_id: str) -> str:
        return f"ecms:session:{self._workspace_id}:{session_id}:"

    def _get_client(self) -> Any:
        import redis
        return redis.Redis(connection_pool=self._pool)

    def set(
        self,
        session_id: str,
        key: str,
        value: Any,
        ttl_seconds: int | None = None,
    ) -> None:
        if not self._available:
            return
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds
        try:
            r = self._get_client()
            r.setex(self._key(session_id, key), ttl, json.dumps(value))
        except Exception as exc:
            logger.warning("Redis session set failed: %s", exc)

    def get(self, session_id: str, key: str, default: Any = None) -> Any:
        if not self._available:
            return default
        try:
            r = self._get_client()
            raw = r.get(self._key(session_id, key))
            return json.loads(raw) if raw is not None else default
        except Exception as exc:
            logger.warning("Redis session get failed: %s", exc)
            return default

    def snapshot(self, session_id: str) -> dict[str, Any]:
        if not self._available:
            return {}
        try:
            r = self._get_client()
            pattern = self._pattern(session_id)
            keys = list(r.scan_iter(match=pattern, count=100))
            result: dict[str, Any] = {}
            prefix = self._prefix(session_id)
            for k in keys:
                raw = r.get(k)
                if raw:
                    short_key = k[len(prefix):]
                    try:
                        result[short_key] = json.loads(raw)
                    except json.JSONDecodeError:
                        result[short_key] = raw
            return result
        except Exception as exc:
            logger.warning("Redis session snapshot failed: %s", exc)
            return {}

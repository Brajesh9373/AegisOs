from datetime import UTC, datetime, timedelta
from typing import Any


class SessionMemory:
    """TTL-backed session memory.

    This in-process implementation mirrors Redis TTL semantics and can be
    swapped for Redis without changing callers.
    """

    def __init__(self, default_ttl_seconds: int = 3600) -> None:
        self.default_ttl_seconds = default_ttl_seconds
        self._sessions: dict[str, tuple[datetime, dict[str, Any]]] = {}

    def set(self, session_id: str, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        expires_at, values = self._sessions.get(session_id, self._new_session(ttl_seconds))
        if expires_at <= datetime.now(UTC):
            expires_at, values = self._new_session(ttl_seconds)
        values[key] = value
        self._sessions[session_id] = (expires_at, values)

    def get(self, session_id: str, key: str, default: Any = None) -> Any:
        session = self._sessions.get(session_id)
        if session is None:
            return default
        expires_at, values = session
        if expires_at <= datetime.now(UTC):
            self._sessions.pop(session_id, None)
            return default
        return values.get(key, default)

    def snapshot(self, session_id: str) -> dict[str, Any]:
        session = self._sessions.get(session_id)
        if session is None:
            return {}
        expires_at, values = session
        if expires_at <= datetime.now(UTC):
            self._sessions.pop(session_id, None)
            return {}
        return dict(values)

    def _new_session(self, ttl_seconds: int | None) -> tuple[datetime, dict[str, Any]]:
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds
        return datetime.now(UTC) + timedelta(seconds=ttl), {}

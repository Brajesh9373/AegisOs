"""Long-term memory — user preferences, frequently used entities.

Layer 7 of the 8-tier memory architecture. Backed by FalkorDB for durability.
Stores user preferences, frequently referenced entities, and learned patterns
that persist across sessions.
"""

from __future__ import annotations

from typing import Any

import falkordb

from legacy_ecms.config import get_settings


class PreferencesStore:
    """FalkorDB-backed preference store. Uses :Preference nodes."""

    def __init__(self, user_id: str = "default") -> None:
        self._user_id = user_id
        self._graph: Any = None

    def _get_graph(self) -> Any:
        if self._graph is None:
            s = get_settings()
            db = falkordb.FalkorDB(
                host=s.falkordb_host, port=s.falkordb_port,
                password=s.falkordb_password or None,
            )
            self._graph = db.select_graph(s.falkordb_database)
        return self._graph

    def set(self, key: str, value: str) -> None:
        """Store a preference. Creates or updates a :Preference node."""
        try:
            g = self._get_graph()
            g.query(
                "MERGE (p:Preference {user_id: $uid, key: $key}) "
                "SET p.value = $value, p.updated_at = timestamp()",
                {"uid": self._user_id, "key": key, "value": value},
            )
        except Exception:
            pass  # Graph down — preference lost but not critical

    def get(self, key: str, default: str = "") -> str:
        """Retrieve a preference value."""
        try:
            g = self._get_graph()
            result = g.query(
                "MATCH (p:Preference {user_id: $uid, key: $key}) RETURN p.value LIMIT 1",
                {"uid": self._user_id, "key": key},
            )
            rows = result.result_set if hasattr(result, "result_set") else result
            if rows and rows[0]:
                return str(rows[0][0])
        except Exception:
            pass
        return default

    def get_all(self) -> dict[str, str]:
        """Return all preferences for this user."""
        try:
            g = self._get_graph()
            result = g.query(
                "MATCH (p:Preference {user_id: $uid}) RETURN p.key, p.value",
                {"uid": self._user_id},
            )
            rows = result.result_set if hasattr(result, "result_set") else result
            return {str(r[0]): str(r[1]) for r in rows if len(r) >= 2}
        except Exception:
            return {}

    def increment_counter(self, key: str) -> int:
        """Increment a usage counter. Used for tracking frequently referenced entities."""
        try:
            g = self._get_graph()
            result = g.query(
                "MERGE (c:Counter {user_id: $uid, key: $key}) "
                "ON CREATE SET c.count = 1 "
                "ON MATCH SET c.count = c.count + 1 "
                "RETURN c.count",
                {"uid": self._user_id, "key": key},
            )
            rows = result.result_set if hasattr(result, "result_set") else result
            if rows and rows[0]:
                return int(rows[0][0])
        except Exception:
            pass
        return 1

    def top_entities(self, limit: int = 10) -> list[dict]:
        """Return most frequently referenced entities."""
        try:
            g = self._get_graph()
            result = g.query(
                "MATCH (c:Counter {user_id: $uid}) "
                "RETURN c.key, c.count ORDER BY c.count DESC LIMIT $limit",
                {"uid": self._user_id, "limit": limit},
            )
            rows = result.result_set if hasattr(result, "result_set") else result
            return [{"entity": str(r[0]), "count": int(r[1])} for r in rows if len(r) >= 2]
        except Exception:
            return []


# ── Singleton ──────────────────────────────────────────────────────────

_store: PreferencesStore | None = None


def get_preferences_store(user_id: str = "default") -> PreferencesStore:
    global _store
    if _store is None:
        _store = PreferencesStore(user_id)
    return _store

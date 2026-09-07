"""Organizational learning — cross-agent shared knowledge via FalkorDB.

Layer 8 of the 8-tier memory architecture. No Kafka dependency.
FalkorDB is the shared bus — all agent instances read/write the same graph.

Pattern: Agent discovers knowledge → writes to :OrganizationalPattern node →
other agents (or next chat) query for validated patterns → all agents benefit.
"""

from __future__ import annotations

from typing import Any


class OrgLearning:
    """Cross-agent knowledge sharing backed by FalkorDB.

    Uses :OrganizationalPattern nodes with properties:
    - pattern_id, pattern_type (best_practice, known_bug, optimization, convention)
    - description, validated_by, validation_count, created_at
    """

    def __init__(self) -> None:
        self._graph: Any = None

    def _get_graph(self) -> Any:
        # Deferred imports: the package must stay importable where falkordb
        # or legacy_ecms are not installed (unit tests, sqlite-only deploys).
        if self._graph is None:
            import falkordb

            from legacy_ecms.config import get_settings

            s = get_settings()
            db = falkordb.FalkorDB(
                host=s.falkordb_host,
                port=s.falkordb_port,
                password=s.falkordb_password or None,
            )
            self._graph = db.select_graph(s.falkordb_database)
        return self._graph

    def publish(self, pattern_type: str, description: str, validated_by: str = "agent") -> str:
        """Publish a validated pattern to the organization. Returns pattern_id."""
        import uuid

        pattern_id = f"org-{pattern_type}-{uuid.uuid4().hex[:8]}"
        try:
            g = self._get_graph()
            g.query(
                "CREATE (p:OrganizationalPattern {"
                "  pattern_id: $pid,"
                "  pattern_type: $ptype,"
                "  description: $desc,"
                "  validated_by: $vby,"
                "  validation_count: 1,"
                "  created_at: timestamp()"
                "})",
                {
                    "pid": pattern_id,
                    "ptype": pattern_type,
                    "desc": description,
                    "vby": validated_by,
                },
            )
            return pattern_id
        except Exception:
            return ""

    def search(
        self, query: str, pattern_type: str | None = None, min_validations: int = 0, limit: int = 10
    ) -> list[dict]:
        """Search organizational patterns by keyword overlap."""
        try:
            g = self._get_graph()
            result = g.query(
                "MATCH (p:OrganizationalPattern) RETURN p.pattern_id, p.pattern_type, p.description, p.validation_count"
            )
            rows = result.result_set if hasattr(result, "result_set") else result
            query_terms = set(query.lower().split())
            all_patterns = []
            for r in rows:
                if len(r) < 4:
                    continue
                pid, ptype, desc, vcount = str(r[0]), str(r[1]), str(r[2]), int(r[3])
                if pattern_type and ptype != pattern_type:
                    continue
                if vcount < min_validations:
                    continue
                desc_terms = set(desc.lower().split())
                if query and not (query_terms & desc_terms):
                    continue
                all_patterns.append(
                    {"id": pid, "type": ptype, "description": desc, "validations": vcount}
                )
            all_patterns.sort(key=lambda p: p["validations"], reverse=True)
            return all_patterns[:limit]
        except Exception:
            return []

    def validate(self, pattern_id: str) -> bool:
        """Increment validation count for an existing pattern."""
        try:
            g = self._get_graph()
            g.query(
                "MATCH (p:OrganizationalPattern {pattern_id: $pid}) "
                "SET p.validation_count = p.validation_count + 1",
                {"pid": pattern_id},
            )
            return True
        except Exception:
            return False

    def top_patterns(self, pattern_type: str = "best_practice", limit: int = 5) -> list[dict]:
        """Get most-validated patterns of a given type."""
        return self.search("", pattern_type=pattern_type, min_validations=1, limit=limit)

    def stats(self) -> dict:
        """Return organizational learning statistics."""
        try:
            g = self._get_graph()
            by_type = g.query(
                "MATCH (p:OrganizationalPattern) "
                "RETURN p.pattern_type, count(p) "
                "ORDER BY count(p) DESC"
            )
            total = g.query("MATCH (p:OrganizationalPattern) RETURN count(p)")
            type_rows = by_type.result_set if hasattr(by_type, "result_set") else by_type
            total_rows = total.result_set if hasattr(total, "result_set") else total
            return {
                "total_patterns": int(total_rows[0][0]) if total_rows else 0,
                "by_type": {str(r[0]): int(r[1]) for r in type_rows if len(r) >= 2},
            }
        except Exception:
            return {"total_patterns": 0, "by_type": {}}


# ── Singleton ──────────────────────────────────────────────────────────

_org: OrgLearning | None = None


def get_org_learning() -> OrgLearning:
    global _org
    if _org is None:
        _org = OrgLearning()
    return _org

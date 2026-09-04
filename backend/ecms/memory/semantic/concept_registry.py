"""Semantic concept registry — interprets business terms over KG + atoms.

Layer 2 of the 8-tier memory architecture. Answers: "What does X mean in this
codebase?" by querying both the atom store (distilled knowledge) and FalkorDB
(raw evidence graph) and merging the results.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import falkordb
from legacy_ecms.config import get_settings
from legacy_ecms.memory.stores.file_store import FileMemoryStore


class ConceptRegistry:
    """Resolves business/technical terms into structured concept objects.

    Queries the atom store for definitions and the graph for relationships.
    Singleton per process — created once, reused across requests.
    """

    def __init__(self) -> None:
        self._store: FileMemoryStore | None = None
        self._graph: Any = None

    def _get_store(self) -> FileMemoryStore:
        if self._store is None:
            self._store = FileMemoryStore(Path("/app/memory"))
        return self._store

    def _get_graph(self) -> Any:
        if self._graph is None:
            s = get_settings()
            db = falkordb.FalkorDB(
                host=s.falkordb_host,
                port=s.falkordb_port,
                password=s.falkordb_password or None,
            )
            self._graph = db.select_graph(s.falkordb_database)
        return self._graph

    async def resolve(self, term: str) -> dict:
        """Resolve a term into a concept: definition, location, relations.

        Returns a dict the agent can use directly.
        """
        result: dict[str, Any] = {
            "term": term,
            "definitions": [],
            "files": [],
            "related": [],
            "synonyms": [],
        }

        # 1. Search atom store for distilled knowledge
        store = self._get_store()
        atoms = store.search_atoms(term, limit=5)
        for a in atoms:
            if a.status.value == "superseded":
                continue
            result["definitions"].append(
                {
                    "summary": a.summary[:300],
                    "type": a.type.value,
                    "confidence": round(a.confidence, 2),
                    "source_atom": a.id,
                }
            )

        # 2. Search FalkorDB for entity locations + relationships
        try:
            g = self._get_graph()
            # Find nodes matching the term
            node_query = await asyncio.to_thread(
                g.query,
                "MATCH (u:UKO) WHERE toLower(u.name) CONTAINS toLower($term) "
                "RETURN u.name, u.type, u.source, u.source_id, u.layer "
                "ORDER BY u.node_confidence DESC LIMIT 15",
                {"term": term},
            )
            rows = node_query.result_set if hasattr(node_query, "result_set") else node_query
            for row in rows:
                name = str(row[0]) if row[0] else ""
                ntype = str(row[1]) if len(row) > 1 and row[1] else ""
                source = str(row[2]) if len(row) > 2 and row[2] else ""
                source_id = str(row[3]) if len(row) > 3 and row[3] else ""
                layer = str(row[4]) if len(row) > 4 and row[4] else ""
                if source_id and source_id not in result["files"]:
                    result["files"].append(source_id)
                if ntype.lower() not in ("unknown", "") and ntype not in result["synonyms"]:
                    result["synonyms"].append(ntype)

            # Find related concepts via RELATES edges
            rel_query = await asyncio.to_thread(
                g.query,
                "MATCH (u:UKO)-[r:RELATES]->(t:UKO) "
                "WHERE toLower(u.name) CONTAINS toLower($term) "
                "RETURN DISTINCT t.name, r.label ORDER BY t.name LIMIT 10",
                {"term": term},
            )
            rel_rows = rel_query.result_set if hasattr(rel_query, "result_set") else rel_query
            for row in rel_rows:
                related_name = str(row[0]) if row[0] else ""
                rel_type = str(row[1]) if len(row) > 1 and row[1] else "related"
                if related_name and related_name != term:
                    result["related"].append({"name": related_name, "relation": rel_type})
        except Exception:
            pass  # Graph unavailable — definitions from atoms are sufficient

        return result

    async def define(self, term: str) -> str:
        """Return a human-readable definition string for the agent."""
        concept = await self.resolve(term)
        lines = [f"## Concept: {concept['term']}"]

        if concept["definitions"]:
            lines.append("\n### From Memory Atoms")
            for d in concept["definitions"]:
                lines.append(f"- [{d['type']}/{d['confidence']:.0%}] {d['summary']}")
        else:
            lines.append("\n_No definition found in memory atoms._")

        if concept["files"]:
            lines.append(f"\n### Defined in ({len(concept['files'])} files)")
            for f in concept["files"][:10]:
                lines.append(f"- {f}")

        if concept["related"]:
            lines.append("\n### Related Concepts")
            for r in concept["related"]:
                lines.append(f"- {r['name']} ({r['relation']})")

        return "\n".join(lines)

    async def define_all(self, terms: list[str]) -> str:
        """Define multiple terms at once. Useful for the agent to get context in bulk."""
        results = []
        for term in terms:
            results.append(await self.define(term))
        return "\n\n".join(results)


# ── Singleton ──────────────────────────────────────────────────────────

_registry: ConceptRegistry | None = None


def get_registry() -> ConceptRegistry:
    global _registry
    if _registry is None:
        _registry = ConceptRegistry()
    return _registry

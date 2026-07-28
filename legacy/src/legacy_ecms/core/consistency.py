import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ConsistencyReport:
    orphan_count: int = 0
    broken_containment_count: int = 0
    unsupported_concept_count: int = 0
    phantom_target_count: int = 0
    type_mismatch_count: int = 0
    total_nodes: int = 0
    orphan_ids: list[str] = field(default_factory=list)
    broken_edge_ids: list[str] = field(default_factory=list)
    unsupported_concept_ids: list[str] = field(default_factory=list)
    phantom_target_ids: list[str] = field(default_factory=list)
    type_mismatch_ids: list[str] = field(default_factory=list)


class ConsistencyChecker:
    """Post-ingestion graph integrity checks for orphan nodes, broken edges,
    phantom stubs, and type mismatches."""

    def __init__(self, graph_client: Any) -> None:
        self.graph = graph_client

    async def check_all(self) -> ConsistencyReport:
        total = await self._count_nodes()
        orphans = await self._find_orphans()
        broken = await self._find_broken_containment()
        unsupported = await self._find_unsupported_concepts()
        phantoms = await self._find_phantom_targets()
        mismatches = await self._find_type_mismatches()

        return ConsistencyReport(
            orphan_count=len(orphans),
            broken_containment_count=len(broken),
            unsupported_concept_count=len(unsupported),
            phantom_target_count=len(phantoms),
            type_mismatch_count=len(mismatches),
            total_nodes=total,
            orphan_ids=orphans,
            broken_edge_ids=broken,
            unsupported_concept_ids=unsupported,
            phantom_target_ids=phantoms,
            type_mismatch_ids=mismatches,
        )

    async def _count_nodes(self) -> int:
        try:
            result = await _query_graph(self.graph, "MATCH (u:UKO) RETURN count(u) AS c")
            rows = result.result_set if hasattr(result, "result_set") else result
            for row in rows:
                return int(row[0]) if row and row[0] else 0
        except Exception as exc:
            logger.warning("Consistency: node count query failed: %s", exc)
        return 0

    async def _find_orphans(self) -> list[str]:
        try:
            result = await _query_graph(
                self.graph,
                "MATCH (u:UKO) WHERE NOT (u)-[:RELATES]-() RETURN u.id LIMIT 1000",
            )
            rows = result.result_set if hasattr(result, "result_set") else result
            return [str(row[0]) for row in rows if row and row[0]]
        except Exception as exc:
            logger.warning("Consistency: orphan query failed: %s", exc)
        return []

    async def _find_broken_containment(self) -> list[str]:
        try:
            result = await _query_graph(
                self.graph,
                "MATCH (u:UKO)-[r:RELATES {label: 'contained_in'}]->(t:UKO) "
                "WHERE NOT t.type IN ['file', 'document'] RETURN u.id LIMIT 1000",
            )
            rows = result.result_set if hasattr(result, "result_set") else result
            return [str(row[0]) for row in rows if row and row[0]]
        except Exception as exc:
            logger.warning("Consistency: broken containment query failed: %s", exc)
        return []

    async def _find_unsupported_concepts(self) -> list[str]:
        try:
            result = await _query_graph(
                self.graph,
                "MATCH (c:UKO {type: 'concept'})-[r1:RELATES {label: 'extracted_from'}]->(:UKO) "
                "WHERE NOT (c)-[:RELATES {label: 'supported_by'}]->(:UKO) "
                "RETURN c.id LIMIT 1000",
            )
            rows = result.result_set if hasattr(result, "result_set") else result
            return [str(row[0]) for row in rows if row and row[0]]
        except Exception as exc:
            logger.warning("Consistency: unsupported concepts query failed: %s", exc)
        return []

    async def _find_phantom_targets(self) -> list[str]:
        try:
            result = await _query_graph(
                self.graph,
                "MATCH (u:UKO)-[r:RELATES]->(t:UKO) "
                "WHERE t.source = '' OR t.name = '' RETURN t.id LIMIT 1000",
            )
            rows = result.result_set if hasattr(result, "result_set") else result
            return [str(row[0]) for row in rows if row and row[0]]
        except Exception as exc:
            logger.warning("Consistency: phantom target query failed: %s", exc)
        return []

    async def _find_type_mismatches(self) -> list[str]:
        try:
            result = await _query_graph(
                self.graph,
                "MATCH (u:UKO)-[r:RELATES {label: 'belongs_to'}]->(t:UKO) "
                "WHERE NOT t.type = 'table' RETURN u.id LIMIT 1000",
            )
            rows = result.result_set if hasattr(result, "result_set") else result
            return [str(row[0]) for row in rows if row and row[0]]
        except Exception as exc:
            logger.warning("Consistency: type mismatch query failed: %s", exc)
        return []

    async def repair(self) -> dict[str, int]:
        deleted = 0
        try:
            result = await _query_graph(
                self.graph,
                "MATCH (u:UKO) WHERE u.source = '' AND NOT (u)-[:RELATES]-() "
                "DELETE u RETURN count(u)",
            )
            rows = result.result_set if hasattr(result, "result_set") else result
            for row in rows:
                deleted = int(row[0]) if row and row[0] else 0
        except Exception as exc:
            logger.warning("Consistency repair failed: %s", exc)

        return {"deleted_orphan_stubs": deleted}


async def _query_graph(graph: Any, query: str, params: dict | None = None) -> Any:
    result = graph.query(query, params or {})
    if hasattr(result, "__await__"):
        return await result
    return result

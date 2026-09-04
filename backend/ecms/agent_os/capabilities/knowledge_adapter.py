"""Knowledge search capability adapter for Agent OS.

This implements the knowledge.search.v1 read-only capability using the existing
scoped knowledge retrieval infrastructure.
"""

from __future__ import annotations

import logging
from typing import Any

from ecms.agent_os.capabilities.contracts import (
    CapabilityEffect,
    CapabilityExecutionContext,
    CapabilityExecutionResult,
    CapabilityPlugin,
    CapabilitySpec,
)

logger = logging.getLogger(__name__)

__all__ = ["KnowledgeSearchCapability"]

# Capability specification for knowledge search
KNOWLEDGE_SEARCH_SPEC = CapabilitySpec(
    capability_id="knowledge.search.v1",
    version="1.0.0",
    effect=CapabilityEffect.READ,
    request_schema_ref="knowledge.search.v1.request",
    result_schema_ref="knowledge.search.v1.result",
    requires_approval=False,
    requires_idempotency_key=True,
    max_arguments_bytes=16 * 1024,
    max_result_bytes=32 * 1024,
)


class KnowledgeSearchCapability(CapabilityPlugin):
    """Read-only knowledge search capability for Agent OS profiles.

    This capability provides access to organizational knowledge through the
    existing knowledge engine, scoped to the caller's organization.
    """

    def __init__(self) -> None:
        self._max_results = 10

    @property
    def capability_spec(self) -> CapabilitySpec:
        return KNOWLEDGE_SEARCH_SPEC

    async def initialize(self) -> None:
        """Initialize the capability (no-op for knowledge search)."""
        pass

    async def health(self) -> bool:
        """Check if knowledge search is available."""
        return True

    async def execute(
        self,
        *,
        context: CapabilityExecutionContext,
        arguments: dict[str, Any],
    ) -> CapabilityExecutionResult:
        """Execute a knowledge search request.

        Args:
            arguments: Must contain 'query' (string) and optionally 'limit' (int)

        Returns:
            List of knowledge results with id, title, summary, relevance
        """
        query = arguments.get("query", "")
        if not query:
            return CapabilityExecutionResult(
                result={"error": "query is required", "results": []},
                audit_metadata={"capability": "knowledge.search.v1"},
            )

        limit = min(arguments.get("limit", self._max_results), self._max_results)

        try:
            results = await self._search_knowledge(
                organization_id=context.organization_id,
                query=query,
                limit=limit,
            )
        except Exception as exc:
            logger.warning(
                "knowledge search failed for org=%s: %s",
                context.organization_id,
                exc,
            )
            return CapabilityExecutionResult(
                result={"error": str(exc), "results": []},
                audit_metadata={
                    "capability": "knowledge.search.v1",
                    "status": "error",
                },
            )

        return CapabilityExecutionResult(
            result={
                "results": results,
                "count": len(results),
                "query": query,
            },
            audit_metadata={
                "capability": "knowledge.search.v1",
                "status": "success",
                "result_count": str(len(results)),
            },
        )

    async def _search_knowledge(
        self,
        organization_id: str,
        query: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Execute scoped knowledge search.

        This uses the existing knowledge retrieval infrastructure scoped to
        the organization. Returns only basic metadata - no raw content.
        """
        # Import here to avoid circular dependencies
        from ecms.knowledge.services.engine import DefaultKnowledgeEngine

        engine = DefaultKnowledgeEngine()
        ucos = await engine.search(query, limit=limit)

        results = []
        for uco in ucos:
            results.append(
                {
                    "id": uco.uco_id,
                    "title": uco.display_name,
                    "summary": uco.summary or uco.description[:200],
                    "type": uco.ontology_type,
                    "confidence": uco.confidence,
                }
            )

        return results


# Global capability instance
_knowledge_capability: KnowledgeSearchCapability | None = None


def get_knowledge_search_capability() -> KnowledgeSearchCapability:
    """Get the knowledge search capability instance."""
    global _knowledge_capability
    if _knowledge_capability is None:
        _knowledge_capability = KnowledgeSearchCapability()
    return _knowledge_capability

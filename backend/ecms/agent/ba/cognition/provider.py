"""Host-side scoped cognition retrieval for Business Analyst DSH execution.

This module is the only data path from authorized knowledge/graph adapters into a
DSH prompt. It intentionally contains no SQL, raw Cypher, legacy-memory singleton,
or process-environment access.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from ecms.agent.ba.cognition.contracts import (
    BAExecutionContext,
    CognitionContextProvider,
    ContextEvidence,
    ContextRetrievalStatus,
    GraphDigest,
    PromptBudget,
    PromptContextPacket,
    PromptMessage,
    RetrievalState,
)

__all__ = [
    "CognitionAuthorizationError",
    "CognitionDependencyUnavailable",
    "NoGraphEvidenceRetriever",
    "ScopedCognitionContextProvider",
    "ScopedGraphEvidenceRetriever",
    "ScopedKnowledgeEvidenceRetriever",
]


class CognitionAuthorizationError(PermissionError):
    """Raised when scope resolution or scoped retrieval is not authorized."""


class CognitionDependencyUnavailable(RuntimeError):  # noqa: N818
    """Raised when an approved retrieval dependency is temporarily unavailable."""


@runtime_checkable
class ScopedKnowledgeEvidenceRetriever(Protocol):
    """Search only knowledge authorized in the storage query itself."""

    async def search(
        self,
        context: BAExecutionContext,
        *,
        query: str,
        limit: int,
    ) -> Sequence[ContextEvidence]:
        """Return already-authorized evidence in best-first relevance order."""


@runtime_checkable
class ScopedGraphEvidenceRetriever(Protocol):
    """Expand only authorized graph seeds without crossing inaccessible nodes."""

    async def expand(
        self,
        context: BAExecutionContext,
        *,
        evidence: tuple[ContextEvidence, ...],
        max_nodes: int,
        max_edges: int,
    ) -> GraphDigest:
        """Return a bounded authorized graph digest originating from evidence seeds."""


@dataclass(frozen=True, slots=True)
class NoGraphEvidenceRetriever:
    """Explicit no-graph adapter for isolated tests and approved non-graph modes."""

    async def expand(
        self,
        context: BAExecutionContext,
        *,
        evidence: tuple[ContextEvidence, ...],
        max_nodes: int,
        max_edges: int,
    ) -> GraphDigest:
        """Return an intentionally empty graph digest without attempting traversal."""
        del context, evidence, max_nodes, max_edges
        return GraphDigest()


class ScopedCognitionContextProvider(CognitionContextProvider):
    """Build a stable bounded packet from query-bound authorization adapters.

    Dependencies must enforce organization, project/workspace, classification,
    lifecycle, and ACL checks while executing their own query/traversal. This class
    adds cardinality and byte budgets; it must never post-filter globally retrieved
    records because that would leak relevance, count, and traversal information.
    """

    def __init__(
        self,
        *,
        knowledge: ScopedKnowledgeEvidenceRetriever,
        graph: ScopedGraphEvidenceRetriever | None = None,
    ) -> None:
        """Initialize the provider with query-bound knowledge and graph adapters."""
        self._knowledge = knowledge
        self._graph = graph

    async def build_packet(
        self,
        context: BAExecutionContext,
        *,
        source_text: str,
        conversation: tuple[PromptMessage, ...],
        budget: PromptBudget,
    ) -> PromptContextPacket:
        """Build a packet, surfacing permitted dependency degradation explicitly."""
        _require_within_budget("source_text", source_text, budget.max_source_bytes)
        _require_conversation_within_budget(conversation, budget.max_conversation_bytes)

        query = _retrieval_query(source_text, conversation)
        statuses: list[ContextRetrievalStatus] = []
        omitted_evidence = 0
        evidence: tuple[ContextEvidence, ...] = ()
        knowledge_available = False
        try:
            retrieved = await self._knowledge.search(
                context, query=query, limit=budget.max_evidence_items
            )
            evidence, omitted_evidence = _bound_evidence(tuple(retrieved), budget)
            knowledge_available = True
            statuses.append(
                ContextRetrievalStatus(
                    source="knowledge",
                    state=RetrievalState.READY,
                    omitted_count=omitted_evidence,
                )
            )
        except CognitionAuthorizationError:
            raise
        except CognitionDependencyUnavailable:
            statuses.append(
                ContextRetrievalStatus(
                    source="knowledge",
                    state=RetrievalState.UNAVAILABLE,
                    reason_code="dependency_unavailable",
                )
            )

        graph = GraphDigest()
        if self._graph is None:
            statuses.append(
                ContextRetrievalStatus(
                    source="graph",
                    state=RetrievalState.UNAVAILABLE,
                    reason_code="not_configured",
                )
            )
        elif not knowledge_available:
            statuses.append(
                ContextRetrievalStatus(
                    source="graph",
                    state=RetrievalState.DEGRADED,
                    reason_code="knowledge_seed_unavailable",
                )
            )
        elif not evidence:
            statuses.append(
                ContextRetrievalStatus(
                    source="graph",
                    state=RetrievalState.DEGRADED,
                    reason_code="no_seeds",
                )
            )
        else:
            try:
                graph = await self._graph.expand(
                    context,
                    evidence=evidence,
                    max_nodes=budget.max_graph_nodes,
                    max_edges=budget.max_graph_edges,
                )
                graph, graph_omissions = _bound_graph(graph, budget)
                statuses.append(
                    ContextRetrievalStatus(
                        source="graph",
                        state=RetrievalState.READY,
                        omitted_count=graph_omissions,
                    )
                )
            except CognitionAuthorizationError:
                raise
            except CognitionDependencyUnavailable:
                statuses.append(
                    ContextRetrievalStatus(
                        source="graph",
                        state=RetrievalState.UNAVAILABLE,
                        reason_code="dependency_unavailable",
                    )
                )

        return PromptContextPacket(
            context=context,
            source_text=source_text,
            conversation=conversation,
            evidence=evidence,
            graph=graph,
            retrieval_statuses=tuple(statuses),
            omitted_evidence_count=omitted_evidence,
        )


def _retrieval_query(source_text: str, conversation: tuple[PromptMessage, ...]) -> str:
    """Build a deterministic retrieval query without invoking a second model."""
    latest_user_text = next(
        (message.content for message in reversed(conversation) if message.role == "user"),
        "",
    )
    return f"{source_text}\n{latest_user_text}".strip()


def _require_within_budget(name: str, value: str, limit: int) -> None:
    """Reject a field that exceeds a byte budget before retrieval or rendering."""
    size = len(value.encode("utf-8"))
    if size > limit:
        raise ValueError(f"{name} exceeds the configured {limit}-byte prompt budget")


def _require_conversation_within_budget(
    conversation: tuple[PromptMessage, ...], limit: int
) -> None:
    """Reject conversation history that cannot be safely placed in a packet."""
    payload = _canonical_json(_conversation_payload(conversation))
    _require_within_budget("conversation", payload, limit)


def _bound_evidence(
    evidence: tuple[ContextEvidence, ...], budget: PromptBudget
) -> tuple[tuple[ContextEvidence, ...], int]:
    """Keep complete best-first evidence records until one exceeds a bound."""
    kept: list[ContextEvidence] = []
    for item in evidence:
        candidate = [*_evidence_payload(tuple(kept)), _evidence_item_payload(item)]
        if (
            len(kept) >= budget.max_evidence_items
            or len(_canonical_json(candidate).encode("utf-8")) > budget.max_evidence_bytes
        ):
            break
        kept.append(item)
    return tuple(kept), len(evidence) - len(kept)


def _bound_graph(graph: GraphDigest, budget: PromptBudget) -> tuple[GraphDigest, int]:
    """Cap graph cardinality and bytes without truncating an individual graph value."""
    nodes = tuple(graph.nodes[: budget.max_graph_nodes])
    edges = tuple(graph.edges[: budget.max_graph_edges])
    bounded = GraphDigest(
        snapshot_version=graph.snapshot_version,
        nodes=nodes,
        edges=edges,
    )
    if len(_canonical_json(_graph_payload(bounded)).encode("utf-8")) > budget.max_graph_bytes:
        # Graph objects are host-generated projections. Do not slice individual
        # fields, because partial values are unreliable evidence and hard to audit.
        return (
            GraphDigest(snapshot_version=graph.snapshot_version),
            len(graph.nodes) + len(graph.edges),
        )
    omissions = (len(graph.nodes) - len(nodes)) + (len(graph.edges) - len(edges))
    return bounded, omissions


def _conversation_payload(conversation: tuple[PromptMessage, ...]) -> list[dict[str, str]]:
    """Return the exact conversation shape emitted by the prompt renderer."""
    return [{"role": message.role, "content": message.content} for message in conversation]


def _evidence_item_payload(item: ContextEvidence) -> dict[str, object]:
    """Return the exact evidence shape emitted by the prompt renderer."""
    return {
        "citation": {
            "id": item.citation.citation_id,
            "kind": item.citation.source_kind,
            "version": item.citation.source_version,
            "trust_state": item.citation.trust_state,
        },
        "classification": item.classification,
        "content": item.content,
    }


def _evidence_payload(evidence: tuple[ContextEvidence, ...]) -> list[dict[str, object]]:
    """Render evidence through the same canonical projection used for sizing."""
    return [_evidence_item_payload(item) for item in evidence]


def _graph_payload(graph: GraphDigest) -> dict[str, object]:
    """Return the exact graph shape emitted by the prompt renderer."""
    return {
        "snapshot_version": graph.snapshot_version,
        "nodes": [dict(item) for item in graph.nodes],
        "edges": [dict(item) for item in graph.edges],
    }


def _canonical_json(value: object) -> str:
    """Serialize host-controlled prompt payloads deterministically for byte limits."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

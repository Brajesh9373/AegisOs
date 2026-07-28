"""Knowledge Graph Reasoning — builds evidence graphs for explainable answers.

Instead of returning isolated memory atoms, the reasoning engine constructs
a connected evidence graph: atoms as nodes, relationships as edges, ranked
by supporting/contradicting evidence quality. The LLM receives a structured
evidence context instead of a flat atom list.

Flow:
  Query → candidate atoms → expand neighborhood → rank evidence →
  prune weak/contradictory → format as evidence graph → LLM context
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from legacy_ecms.memory.domain import (
    MemoryAtom,
    MemoryRelationship,
    MemoryStatus,
    RelationshipType,
    ScoredAtom,
)
from legacy_ecms.memory.interfaces import MemoryStore


# ── Evidence Graph Nodes & Edges ────────────────────────────────────

@dataclass
class EvidenceNode:
    """A node in the evidence graph — wraps a memory atom with metadata."""

    atom: MemoryAtom
    role: str = "evidence"  # primary | supporting | contradicting | reference
    score: float = 0.0
    hop_distance: int = 0  # 0 = primary candidate, 1 = directly related, 2+ = indirect

    @property
    def id(self) -> str:
        return self.atom.id


@dataclass
class EvidenceEdge:
    """An edge in the evidence graph — a relationship between two nodes."""

    source_id: str
    target_id: str
    type: RelationshipType
    confidence: float
    evidence: list[str] = field(default_factory=list)

    @property
    def is_supporting(self) -> bool:
        """Is this edge supporting evidence (vs contradicting/weakening)?"""
        return self.type not in (
            RelationshipType.CONTRADICTS,
            RelationshipType.SUPERSEDES,
        )

    @property
    def is_contradicting(self) -> bool:
        return self.type == RelationshipType.CONTRADICTS


@dataclass
class EvidenceGraph:
    """A connected evidence graph built from memory atoms and relationships."""

    query: str
    primary_nodes: list[EvidenceNode] = field(default_factory=list)
    supporting_nodes: list[EvidenceNode] = field(default_factory=list)
    contradicting_nodes: list[EvidenceNode] = field(default_factory=list)
    edges: list[EvidenceEdge] = field(default_factory=list)
    total_candidates: int = 0
    pruned_count: int = 0
    execution_ms: float = 0.0

    def all_nodes(self) -> list[EvidenceNode]:
        return self.primary_nodes + self.supporting_nodes + self.contradicting_nodes

    def node_count(self) -> int:
        return len(self.all_nodes())

    def edge_count(self) -> int:
        return len(self.edges)

    def summary(self) -> dict[str, Any]:
        return {
            "primary": len(self.primary_nodes),
            "supporting": len(self.supporting_nodes),
            "contradicting": len(self.contradicting_nodes),
            "edges": len(self.edges),
            "pruned": self.pruned_count,
            "total_candidates": self.total_candidates,
            "execution_ms": self.execution_ms,
        }


# ── Evidence Graph Builder ──────────────────────────────────────────

class EvidenceGraphBuilder:
    """Builds an evidence graph from scored atoms by expanding their
    relationship neighborhood.

    Attributes:
        store: Memory store for atom/relationship lookups.
        max_depth: Maximum BFS hops for expansion.
        max_supporting: Maximum supporting nodes to include.
        min_confidence: Minimum atom confidence to include.
        min_edge_confidence: Minimum relationship confidence to traverse.
    """

    def __init__(
        self,
        store: MemoryStore,
        max_depth: int = 2,
        max_supporting: int = 12,
        min_confidence: float = 0.50,
        min_edge_confidence: float = 0.50,
    ) -> None:
        self.store = store
        self.max_depth = max_depth
        self.max_supporting = max_supporting
        self.min_confidence = min_confidence
        self.min_edge_confidence = min_edge_confidence

    def build(self, query: str, candidates: list[ScoredAtom]) -> EvidenceGraph:
        """Build an evidence graph from scored retrieval candidates.

        Args:
            query: The original user query.
            candidates: Scored atoms from the retrieval pipeline.

        Returns:
            A connected EvidenceGraph with primary, supporting, and contradicting nodes.
        """
        import time
        start = time.perf_counter()

        graph = EvidenceGraph(query=query, total_candidates=len(candidates))

        if not candidates:
            return graph

        # Step 1 — Add primary nodes (top candidates)
        seen_ids: set[str] = set()
        for sc in candidates[:5]:
            if sc.atom.confidence < self.min_confidence:
                continue
            node = EvidenceNode(
                atom=sc.atom,
                role="primary",
                score=sc.score,
                hop_distance=0,
            )
            graph.primary_nodes.append(node)
            seen_ids.add(sc.atom.id)

        # Step 2 — BFS expansion
        from collections import deque
        queue: deque[tuple[str, int]] = deque()
        for pn in graph.primary_nodes:
            queue.append((pn.id, 0))

        while queue:
            current_id, current_depth = queue.popleft()
            if current_depth >= self.max_depth:
                continue

            for rel in self.store.get_relationships(current_id):
                if rel.confidence < self.min_edge_confidence:
                    continue

                neighbor_id = (
                    rel.target_id if rel.source_id == current_id
                    else rel.source_id
                )
                if neighbor_id in seen_ids:
                    # Already in graph — just add the edge
                    graph.edges.append(EvidenceEdge(
                        source_id=rel.source_id,
                        target_id=rel.target_id,
                        type=rel.type,
                        confidence=rel.confidence,
                        evidence=rel.evidence,
                    ))
                    continue

                neighbor = self.store.get_atom(neighbor_id)
                if neighbor is None or neighbor.confidence < self.min_confidence:
                    continue
                if neighbor.status == MemoryStatus.SUPERSEDED:
                    continue

                seen_ids.add(neighbor_id)

                # Classify role
                edge = EvidenceEdge(
                    source_id=rel.source_id,
                    target_id=rel.target_id,
                    type=rel.type,
                    confidence=rel.confidence,
                    evidence=rel.evidence,
                )
                graph.edges.append(edge)

                node = EvidenceNode(
                    atom=neighbor,
                    role="supporting" if edge.is_supporting else "contradicting",
                    score=neighbor.computed_confidence(),
                    hop_distance=current_depth + 1,
                )

                if edge.is_contradicting:
                    graph.contradicting_nodes.append(node)
                else:
                    if len(graph.supporting_nodes) < self.max_supporting:
                        graph.supporting_nodes.append(node)
                        queue.append((neighbor_id, current_depth + 1))

        graph.execution_ms = round((time.perf_counter() - start) * 1000, 2)
        return graph


# ── Evidence Ranker ─────────────────────────────────────────────────

class EvidenceRanker:
    """Ranks evidence nodes by multiple quality factors.

    Factors (all configurable):
        - Base confidence
        - Evidence quality
        - Status (verified > draft > superseded)
        - Evidence source weight
        - Relationship depth penalty
    """

    def __init__(
        self,
        depth_penalty: float = 0.15,
        verified_boost: float = 0.10,
        draft_penalty: float = 0.10,
        source_code_boost: float = 0.05,
    ) -> None:
        self.depth_penalty = depth_penalty
        self.verified_boost = verified_boost
        self.draft_penalty = draft_penalty
        self.source_code_boost = source_code_boost

    def rank(self, graph: EvidenceGraph) -> EvidenceGraph:
        """Rank all nodes in the graph by evidence quality.

        Modifies graph.supporting_nodes and graph.contradicting_nodes
        in place with updated scores.
        """
        for node in graph.all_nodes():
            score = node.atom.computed_confidence()

            # Depth penalty
            score -= node.hop_distance * self.depth_penalty

            # Status boost/penalty
            if node.atom.status == MemoryStatus.VERIFIED:
                score += self.verified_boost
            elif node.atom.status == MemoryStatus.DRAFT:
                score -= self.draft_penalty

            # Source code evidence boost
            for ev in node.atom.evidence:
                if ev.source_type.value == "source_code":
                    score += self.source_code_boost
                    break

            node.score = max(0.0, min(1.0, score))

        # Re-sort supporting nodes by score descending
        graph.supporting_nodes.sort(key=lambda n: n.score, reverse=True)
        graph.contradicting_nodes.sort(key=lambda n: n.score, reverse=True)
        return graph


# ── Evidence Pruner ─────────────────────────────────────────────────

class EvidencePruner:
    """Prunes weak, redundant, or contradictory evidence from the graph.

    Rules:
        - Remove nodes below min_score
        - Keep at most max_supporting supporting nodes
        - Flag but preserve contradicting evidence
    """

    def __init__(
        self,
        max_supporting: int = 8,
        min_score: float = 0.30,
    ) -> None:
        self.max_supporting = max_supporting
        self.min_score = min_score

    def prune(self, graph: EvidenceGraph) -> EvidenceGraph:
        """Prune the graph in place and return it."""
        before = len(graph.supporting_nodes)

        # Trim supporting nodes
        graph.supporting_nodes = [
            n for n in graph.supporting_nodes if n.score >= self.min_score
        ]
        graph.supporting_nodes = graph.supporting_nodes[:self.max_supporting]

        # Trim contradicting nodes
        graph.contradicting_nodes = [
            n for n in graph.contradicting_nodes if n.score >= self.min_score
        ]

        # Trim edges to match remaining nodes
        remaining_ids = {n.id for n in graph.all_nodes()}
        graph.edges = [
            e for e in graph.edges
            if e.source_id in remaining_ids and e.target_id in remaining_ids
        ]

        graph.pruned_count = before - len(graph.supporting_nodes)
        return graph


# ── Evidence Formatter ──────────────────────────────────────────────

def format_evidence_graph(graph: EvidenceGraph) -> str:
    """Format an evidence graph as structured context for the LLM prompt.

    Produces a rich, connected view:
      - Primary claims (from retrieval)
      - Supporting evidence (related, derived, implements)
      - Contradictory evidence (if any, with explanation)
      - Relationship summary

    The output is designed to maximize reasoning quality while
    minimizing prompt length.
    """
    if not graph.primary_nodes:
        return ""

    lines = ["", "=" * 32, "Evidence Graph", "=" * 32, ""]

    # Primary claims
    for i, node in enumerate(graph.primary_nodes, 1):
        a = node.atom
        status = "✓" if a.status.value == "verified" else "○"
        lines.append(f"[{i}] PRIMARY  {a.id}  [{a.type.value.upper()}]  confidence={a.confidence:.0%}  {status}")
        lines.append(f"    {a.summary[:300]}")

    # Supporting evidence (grouped by relationship type)
    if graph.supporting_nodes:
        lines.append("")
        lines.append(f"--- Supporting Evidence ({len(graph.supporting_nodes)} nodes) ---")
        for node in graph.supporting_nodes:
            a = node.atom
            # Find the relationship connecting this node
            rel_type = "related_to"
            for e in graph.edges:
                if e.target_id == node.id or e.source_id == node.id:
                    if e.is_supporting:
                        rel_type = e.type.value
                        break
            lines.append(f"  [{rel_type}] {a.id}  [{a.type.value.upper()}]  score={node.score:.0%}  {a.summary[:200]}")

    # Contradictory evidence
    if graph.contradicting_nodes:
        lines.append("")
        lines.append(f"--- Contradictory Evidence ({len(graph.contradicting_nodes)} nodes) ---")
        lines.append("  ⚠ The following atoms CONTRADICT claims above:")
        for node in graph.contradicting_nodes:
            lines.append(f"  ⚠ {node.id}  [{node.atom.type.value.upper()}]  {node.atom.summary[:200]}")

    # Summary
    lines.append("")
    lines.append(f"Graph: {graph.node_count()} nodes, {graph.edge_count()} edges")
    if graph.pruned_count:
        lines.append(f"(pruned {graph.pruned_count} weak nodes)")

    return "\n".join(lines)


# ── Full Reasoning Pipeline ─────────────────────────────────────────

class ReasoningPipeline:
    """End-to-end evidence graph construction pipeline.

    Usage:
        pipeline = ReasoningPipeline(store)
        graph = pipeline.reason(query, candidates)
        context = format_evidence_graph(graph)
    """

    def __init__(
        self,
        store: MemoryStore,
        max_depth: int = 2,
        max_supporting: int = 8,
    ) -> None:
        self.store = store
        self.builder = EvidenceGraphBuilder(
            store, max_depth=max_depth, max_supporting=max_supporting,
        )
        self.ranker = EvidenceRanker()
        self.pruner = EvidencePruner(max_supporting=max_supporting)

    def reason(self, query: str, candidates: list[ScoredAtom]) -> EvidenceGraph:
        """Build, rank, and prune an evidence graph from scored candidates."""
        graph = self.builder.build(query, candidates)
        graph = self.ranker.rank(graph)
        graph = self.pruner.prune(graph)
        return graph

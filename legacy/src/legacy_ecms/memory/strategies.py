"""Pluggable retrieval strategies.

Each strategy is an independent callable that scores/re-ranks candidates.
The pipeline composes strategies without knowing how each works internally.

All strategies operate on the MemoryStore protocol — storage-agnostic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from legacy_ecms.memory.domain import MemoryAtom, ScoredAtom
from legacy_ecms.memory.interfaces import MemoryStore


# ── Strategy Protocol ───────────────────────────────────────────────

class RetrievalStrategy(ABC):
    """Abstract retrieval strategy — pluggable into the pipeline."""

    name: str = "base"

    @abstractmethod
    async def apply(
        self,
        query: str,
        candidates: list[ScoredAtom],
        store: MemoryStore,
        **kwargs: Any,
    ) -> list[ScoredAtom]:
        """Transform/re-rank candidates. Return modified list."""
        ...


class KeywordStrategy(RetrievalStrategy):
    """Broad recall via keyword matching over topic + summary + tags."""

    name = "keyword"

    async def apply(
        self,
        query: str,
        candidates: list[ScoredAtom],  # ignored — broad recall
        store: MemoryStore,
        **kwargs: Any,
    ) -> list[ScoredAtom]:
        limit = kwargs.get("keyword_limit", 30)
        atoms = store.search_atoms(query, limit=limit)
        return [
            ScoredAtom(atom=a, score=0.0, score_breakdown={"keyword": 0.5})
            for a in atoms
        ]


class SemanticStrategy(RetrievalStrategy):
    """Semantic similarity search via embedding index.

    Requires an EmbeddingIndex passed via kwargs at pipeline construction.
    """

    name = "semantic"

    def __init__(self, embeddings: Any = None) -> None:
        """embedding_index must support .search(query, top_k) → [(id, score)]."""
        self._embedding_index = embeddings  # EmbeddingIndex or similar

    async def apply(
        self,
        query: str,
        candidates: list[ScoredAtom],
        store: MemoryStore,
        **kwargs: Any,
    ) -> list[ScoredAtom]:
        if self._embedding_index is None:
            return candidates

        top_k = kwargs.get("semantic_top_k", 15)
        sim_threshold = kwargs.get("semantic_threshold", 0.3)

        results = self._embedding_index.search(query, top_k=top_k)

        # Convert (id, score) → ScoredAtom if atom exists
        semantic_atoms: dict[str, float] = {}
        for atom_id, sim_score in results:
            if sim_score >= sim_threshold:
                semantic_atoms[atom_id] = sim_score

        # Boost existing candidates with semantic scores
        for sc in candidates:
            if sc.atom.id in semantic_atoms:
                sem_score = semantic_atoms[sc.atom.id]
                sc.score = (sc.score or 0.0) + sem_score * 0.3
                sc.score_breakdown["semantic"] = sem_score
                del semantic_atoms[sc.atom.id]

        # Add purely semantic hits not already in candidates
        for atom_id, sim_score in semantic_atoms.items():
            atom = store.get_atom(atom_id)
            if atom:
                candidates.append(
                    ScoredAtom(
                        atom=atom,
                        score=sim_score * 0.3,
                        score_breakdown={"semantic": sim_score},
                    )
                )

        return candidates


class RelationshipExpandStrategy(RetrievalStrategy):
    """Expand candidates by traversing graph relationships (BFS)."""

    name = "relationship_expand"

    async def apply(
        self,
        query: str,
        candidates: list[ScoredAtom],
        store: MemoryStore,
        **kwargs: Any,
    ) -> list[ScoredAtom]:
        max_hops = kwargs.get("relationship_hops", 1)
        expanded_ids: set[str] = {sc.atom.id for sc in candidates}
        for sc in list(candidates):
            related = store.get_related_atoms(sc.atom.id, depth=max_hops)
            for related_atom in related:
                if related_atom.id not in expanded_ids:
                    expanded_ids.add(related_atom.id)
                    candidates.append(
                        ScoredAtom(
                            atom=related_atom,
                            score=0.0,
                            score_breakdown={"relationship_expand": 0.3},
                        )
                    )
        return candidates


class ConfidenceRankStrategy(RetrievalStrategy):
    """Rank by atom.confidence * evidence_quality.

    Boosts verified atoms and penalizes draft/superseded ones.
    """

    name = "confidence_rank"

    async def apply(
        self,
        query: str,
        candidates: list[ScoredAtom],
        store: MemoryStore,
        **kwargs: Any,
    ) -> list[ScoredAtom]:
        for sc in candidates:
            a = sc.atom
            confidence_score = a.computed_confidence()

            # Boost verified atoms
            if a.status.value == "verified":
                confidence_score *= 1.1
            elif a.status.value == "draft":
                confidence_score *= 0.9

            # Boost recently validated atoms
            if a.validated_at:
                try:
                    from datetime import datetime, timezone, timedelta
                    validated = datetime.fromisoformat(a.validated_at.replace("Z", "+00:00"))
                    age_days = (datetime.now(timezone.utc) - validated).days
                    if age_days < 7:
                        confidence_score *= 1.05  # Recently validated → boost
                    elif age_days > 90:
                        confidence_score *= 0.95  # Stale → slight penalty
                except (ValueError, TypeError):
                    pass

            sc.score = (sc.score or 0.0) + confidence_score * 0.5
            sc.score_breakdown["confidence"] = confidence_score

        candidates.sort(key=lambda s: s.score, reverse=True)
        return candidates


class EvidenceQualityRankStrategy(RetrievalStrategy):
    """Rank by evidence quality — source code > docs > memory > conversation."""

    name = "evidence_quality"

    async def apply(
        self,
        query: str,
        candidates: list[ScoredAtom],
        store: MemoryStore,
        **kwargs: Any,
    ) -> list[ScoredAtom]:
        for sc in candidates:
            eq = sc.atom.evidence_quality()
            sc.score = (sc.score or 0.0) + eq * 0.2
            sc.score_breakdown["evidence_quality"] = eq

        candidates.sort(key=lambda s: s.score, reverse=True)
        return candidates


class BudgetTrimStrategy(RetrievalStrategy):
    """Trim to budget using type-diverse selection."""

    name = "budget_trim"

    async def apply(
        self,
        query: str,
        candidates: list[ScoredAtom],
        store: MemoryStore,
        **kwargs: Any,
    ) -> list[ScoredAtom]:
        from legacy_ecms.memory.retrieval import RetrievalBudget

        budget = kwargs.get("budget", RetrievalBudget.default())
        type_counts: dict[str, int] = {}
        selected: list[ScoredAtom] = []

        for sc in candidates:
            if len(selected) >= budget.max_total:
                break
            atype = sc.atom.type.value
            slots = budget.type_slots.get(atype, 1)
            current = type_counts.get(atype, 0)
            if current < slots:
                selected.append(sc)
                type_counts[atype] = current + 1

        return selected


# ── Metadata filter strategy (future extension point) ──────────────

class MetadataFilterStrategy(RetrievalStrategy):
    """Filter candidates by scope, tag, or date range.

    Extensible — add new filters by overriding _passes_filter.
    """

    name = "metadata_filter"

    async def apply(
        self,
        query: str,
        candidates: list[ScoredAtom],
        store: MemoryStore,
        **kwargs: Any,
    ) -> list[ScoredAtom]:
        scope = kwargs.get("scope")
        tag = kwargs.get("tag")
        min_confidence = kwargs.get("min_confidence")

        def passes(a: MemoryAtom) -> bool:
            if scope and a.scope.value != scope:
                return False
            if tag and tag not in a.tags:
                return False
            if min_confidence and a.confidence < min_confidence:
                return False
            return True

        return [sc for sc in candidates if passes(sc.atom)]

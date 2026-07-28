"""Recomposable retrieval pipeline — strategies are pluggable, configurable.

Usage:
    pipeline = RetrievalPipeline(store)
    pipeline.add_strategy(KeywordStrategy())
    pipeline.add_strategy(SemanticStrategy(embedding_index))
    pipeline.add_strategy(ConfidenceRankStrategy())
    pipeline.add_strategy(BudgetTrimStrategy())
    result = await pipeline.retrieve(query, budget=budget)
"""

from __future__ import annotations

import time
from typing import Any

from legacy_ecms.memory.domain import RetrievalResult, ScoredAtom
from legacy_ecms.memory.interfaces import MemoryStore
from legacy_ecms.memory.strategies import (
    BudgetTrimStrategy,
    ConfidenceRankStrategy,
    EvidenceQualityRankStrategy,
    KeywordStrategy,
    MetadataFilterStrategy,
    RelationshipExpandStrategy,
    RetrievalStrategy,
    SemanticStrategy,
)


# ── Usage tracker ──────────────────────────────────────────────────

class UsageTracker:
    """Tracks how many times each atom has been retrieved.

    Simple in-memory counter. At scale, replace with Redis or a DB table.
    """

    def __init__(self) -> None:
        self._counts: dict[str, int] = {}

    def record(self, atom_ids: list[str]) -> None:
        for aid in atom_ids:
            self._counts[aid] = self._counts.get(aid, 0) + 1

    def get_count(self, atom_id: str) -> int:
        return self._counts.get(atom_id, 0)

    def snapshot(self) -> dict[str, int]:
        return dict(self._counts)


class RetrievalBudget:
    """Configurable retrieval budget — limits atoms by type and total count."""

    def __init__(
        self,
        max_total: int = 8,
        type_slots: dict[str, int] | None = None,
    ) -> None:
        self.max_total = max_total
        self.type_slots: dict[str, int] = type_slots or {
            "fact": 2,
            "architecture": 2,
            "decision": 1,
            "convention": 1,
            "observation": 1,
            "bug": 1,
            "limitation": 1,
            "security": 1,
            "best_practice": 1,
            "performance": 1,
        }

    @classmethod
    def default(cls) -> "RetrievalBudget":
        return cls()

    @classmethod
    def tight(cls) -> "RetrievalBudget":
        return cls(max_total=4, type_slots={
            "fact": 2, "architecture": 1, "decision": 1,
        })

    @classmethod
    def generous(cls) -> "RetrievalBudget":
        return cls(max_total=16, type_slots={
            "fact": 4, "architecture": 3, "decision": 2, "convention": 2,
            "observation": 2, "bug": 2, "limitation": 2, "security": 2,
            "best_practice": 2, "performance": 2,
        })


class RetrievalPipeline:
    """Recomposable hybrid retrieval pipeline.

    Strategies are added in order. Each strategy transforms the candidate
    list. The pipeline owns no state beyond strategy composition.
    """

    def __init__(self, store: MemoryStore) -> None:
        self.store = store
        self._strategies: list[RetrievalStrategy] = []
        self.usage_tracker = UsageTracker()

    def add_strategy(self, strategy: RetrievalStrategy) -> "RetrievalPipeline":
        """Add a strategy to the pipeline. Returns self for chaining."""
        self._strategies.append(strategy)
        return self

    @classmethod
    def default_pipeline(cls, store: MemoryStore) -> "RetrievalPipeline":
        """Create a pipeline with the standard production strategy chain."""
        return (
            cls(store)
            .add_strategy(KeywordStrategy())
            .add_strategy(RelationshipExpandStrategy())
            .add_strategy(ConfidenceRankStrategy())
            .add_strategy(EvidenceQualityRankStrategy())
            .add_strategy(BudgetTrimStrategy())
        )

    @classmethod
    def semantic_pipeline(
        cls, store: MemoryStore, embeddings: Any = None
    ) -> "RetrievalPipeline":
        """Create a pipeline with semantic search enabled."""
        return (
            cls(store)
            .add_strategy(KeywordStrategy())
            .add_strategy(SemanticStrategy(embeddings))
            .add_strategy(RelationshipExpandStrategy())
            .add_strategy(ConfidenceRankStrategy())
            .add_strategy(EvidenceQualityRankStrategy())
            .add_strategy(BudgetTrimStrategy())
        )

    async def retrieve(
        self,
        query: str,
        budget: RetrievalBudget | None = None,
        **kwargs: Any,
    ) -> RetrievalResult:
        """Run all strategies in order on the query.

        KeywordStrategy produces initial candidates. Subsequent strategies
        transform/re-rank the candidate list. Budget trimming is always last
        if present.
        """
        budget = budget or RetrievalBudget.default()
        start = time.perf_counter()
        strategies_used: list[str] = []
        candidates: list[ScoredAtom] = []

        # Separate BudgetTrimStrategy — always runs last
        budget_strategy = None
        run_strategies: list[RetrievalStrategy] = []
        for s in self._strategies:
            if isinstance(s, BudgetTrimStrategy):
                budget_strategy = s
            else:
                run_strategies.append(s)

        for strategy in run_strategies:
            strategies_used.append(strategy.name)
            candidates = await strategy.apply(
                query, candidates, self.store, budget=budget, **kwargs
            )

        # Deduplicate by atom ID (keep highest-scored)
        seen: dict[str, ScoredAtom] = {}
        for sc in candidates:
            aid = sc.atom.id
            if aid not in seen or sc.score > seen[aid].score:
                seen[aid] = sc
        candidates = sorted(seen.values(), key=lambda s: s.score, reverse=True)

        # Budget trim (runs last if present)
        total_candidates = len(candidates)
        if budget_strategy:
            candidates = await budget_strategy.apply(
                query, candidates, self.store, budget=budget, **kwargs
            )
            strategies_used.append(budget_strategy.name)

        elapsed = (time.perf_counter() - start) * 1000
        return RetrievalResult(
            query=query,
            atoms=candidates,
            total_candidates=total_candidates,
            strategies_used=strategies_used,
            execution_ms=round(elapsed, 2),
        )


# ── Prompt formatter ────────────────────────────────────────────────

def format_retrieval_for_prompt(result: RetrievalResult) -> str:
    """Format a RetrievalResult as structured memory blocks for the LLM prompt."""
    if not result.atoms:
        return ""

    lines = ["", "=" * 28, "Retrieved Memory", "=" * 28, ""]
    for sc in result.atoms:
        a = sc.atom
        icon = (
            "✓" if a.status.value == "verified"
            else "○" if a.status.value == "draft"
            else "⚠"
        )
        validated = (
            f"Validated: {a.validated_at[:10]}" if a.validated_at else "Unvalidated"
        )
        quality = a.evidence_quality()
        lines.append(
            f"┌─ {a.id}  [{a.type.value.upper()}]  confidence={a.confidence:.0%}  "
            f"evidence_quality={quality:.0%}  {icon} {a.status.value}"
        )
        lines.append(f"│  Topic: {a.topic}")
        lines.append(f"│  {a.summary[:400]}")
        if a.evidence:
            sources = [e.source for e in a.evidence[:3]]
            lines.append(f"│  Evidence: {', '.join(sources)}")
        if a.related_atoms:
            rels = ", ".join(
                f"{r.atom_id}({r.type.value})" for r in a.related_atoms[:3]
            )
            lines.append(f"│  Related: {rels}")
        lines.append(f"│  Version: {a.version}  |  {validated}")
        lines.append("└" + "─" * 26)
        lines.append("")

    return "\n".join(lines)

"""Adaptive confidence engine — dynamic scoring with configurable boost/decay.

Confidence is no longer static. It adapts based on:
  - Evidence quality (how strong is the supporting evidence)
  - Usage frequency (how often is this atom retrieved)
  - Recency (was it recently validated)
  - Corroboration (do other atoms support or contradict it)
  - Staleness (has it gone unvalidated too long)
  - Contradictions (are there known conflicting atoms)
  - User confirmation (has it been explicitly verified)

All factors are configurable via ConfidenceConfig. No hardcoded constants.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any

from legacy_ecms.memory.domain import MemoryAtom, MemoryStatus, RelationshipType
from legacy_ecms.memory.interfaces import MemoryStore


# ── Configuration ───────────────────────────────────────────────────

@dataclass
class ConfidenceConfig:
    """All boost/decay factors are configurable — no hardcoded values."""

    # Base range
    min_confidence: float = 0.10
    max_confidence: float = 1.0

    # Evidence quality weight (how much evidence_quality affects confidence)
    evidence_weight: float = 0.35

    # Usage boost — per retrieval, atom gains this much (capped)
    usage_boost_per_retrieval: float = 0.005
    usage_boost_cap: float = 0.10

    # Recency boost — if validated within recent_days
    recency_boost: float = 0.05
    recent_days: int = 7

    # Corroboration — if other atoms support this one, boost
    corroboration_boost: float = 0.03
    corroboration_min_supporters: int = 1

    # Staleness decay — per day beyond staleness_threshold_days
    staleness_decay_per_day: float = 0.01
    staleness_threshold_days: int = 30

    # Contradiction penalty — if contradictions exist, reduce
    contradiction_penalty: float = 0.15

    # User confirmation — explicit verification gives a strong boost
    user_confirmation_boost: float = 0.20

    # Superseded penalty
    superseded_penalty: float = 0.50

    # Default if no data available
    default_confidence: float = 0.70


# ── Engine ──────────────────────────────────────────────────────────

@dataclass
class ConfidenceAdjustment:
    """Transparent adjustment to an atom's confidence."""

    atom_id: str
    old_confidence: float
    new_confidence: float
    factors: dict[str, float] = field(default_factory=dict)
    reasoning: list[str] = field(default_factory=list)

    def explain(self) -> str:
        lines = [
            f"{self.atom_id}: {self.old_confidence:.0%} → {self.new_confidence:.0%}",
        ]
        for factor, delta in self.factors.items():
            sign = "+" if delta >= 0 else ""
            lines.append(f"  {sign}{delta:+.0%}  {factor}")
        for r in self.reasoning:
            lines.append(f"  ∴ {r}")
        return "\n".join(lines)


class ConfidenceEngine:
    """Computes dynamic confidence for a memory atom based on its
    current state, evidence quality, usage, and relationship context.
    """

    def __init__(self, config: ConfidenceConfig | None = None) -> None:
        self.config = config or ConfidenceConfig()

    def compute(
        self,
        atom: MemoryAtom,
        store: MemoryStore | None = None,
        retrieval_count: int = 0,
        user_confirmed: bool = False,
    ) -> ConfidenceAdjustment:
        """Compute the adjusted confidence for a single atom.

        Args:
            atom: The atom to evaluate.
            store: Optional store for relationship context.
            retrieval_count: How many times this atom has been retrieved (usage tracking).
            user_confirmed: Whether the user has explicitly verified this atom.

        Returns:
            ConfidenceAdjustment with old/new values and explanation.
        """
        old = atom.confidence
        factors: dict[str, float] = {}
        reasoning: list[str] = []

        # Start from evidence-adjusted baseline
        eq = atom.evidence_quality()
        base = atom.confidence * (1.0 - self.config.evidence_weight) + eq * self.config.evidence_weight

        # 1. Evidence quality
        ev_delta = base - old
        if abs(ev_delta) > 0.01:
            factors["evidence_quality"] = ev_delta
            reasoning.append(f"Evidence quality {eq:.0%} adjusts base by {ev_delta:+.0%}")

        # 2. Usage boost
        if retrieval_count > 0:
            usage = min(self.config.usage_boost_cap, retrieval_count * self.config.usage_boost_per_retrieval)
            factors["usage"] = usage
            reasoning.append(f"Retrieved {retrieval_count} times → +{usage:.0%}")

        # 3. Recency boost
        if atom.validated_at:
            try:
                validated = datetime.fromisoformat(atom.validated_at.replace("Z", "+00:00"))
                age_days = (datetime.now(timezone.utc) - validated).days
                if age_days <= self.config.recent_days:
                    factors["recency"] = self.config.recency_boost
                    reasoning.append(f"Validated {age_days}d ago → +{self.config.recency_boost:.0%}")
                elif age_days > self.config.staleness_threshold_days:
                    decay = -((age_days - self.config.staleness_threshold_days) * self.config.staleness_decay_per_day)
                    decay = max(decay, -(old * 0.5))
                    factors["staleness"] = decay
                    reasoning.append(f"Stale ({age_days}d) → {decay:+.0%}")
            except (ValueError, TypeError):
                pass

        # 4. Status-based adjustments
        if atom.status == MemoryStatus.SUPERSEDED:
            factors["superseded"] = -self.config.superseded_penalty
            reasoning.append(f"Superseded → -{self.config.superseded_penalty:.0%}")

        # 5. Corroboration / contradiction (requires store)
        if store:
            supporting = 0
            contradicting = 0
            for rel in store.get_relationships(atom.id):
                if rel.type == RelationshipType.CONTRADICTS:
                    contradicting += 1
                elif rel.type.value in ("supports", "implements", "derived_from"):
                    supporting += 1

            if supporting >= self.config.corroboration_min_supporters:
                factors["corroboration"] = self.config.corroboration_boost * min(supporting, 5)
                reasoning.append(f"Supported by {supporting} atoms → +{factors['corroboration']:.0%}")
            if contradicting > 0:
                factors["contradiction"] = -self.config.contradiction_penalty * contradicting
                reasoning.append(f"Contradicted by {contradicting} atoms → {factors['contradiction']:+.0%}")

        # 6. User confirmation
        if user_confirmed:
            factors["user_confirmed"] = self.config.user_confirmation_boost
            reasoning.append(f"Explicitly verified → +{self.config.user_confirmation_boost:.0%}")

        # Compute final confidence
        new = old
        for delta in factors.values():
            new += delta

        # Clamp
        new = max(self.config.min_confidence, min(self.config.max_confidence, new))
        new = round(new, 4)

        return ConfidenceAdjustment(
            atom_id=atom.id,
            old_confidence=old,
            new_confidence=new,
            factors=factors,
            reasoning=reasoning,
        )

    def compute_batch(
        self,
        atoms: list[MemoryAtom],
        store: MemoryStore | None = None,
        retrieval_counts: dict[str, int] | None = None,
    ) -> list[ConfidenceAdjustment]:
        """Compute adjusted confidence for multiple atoms at once."""
        counts = retrieval_counts or {}
        return [
            self.compute(atom, store, counts.get(atom.id, 0))
            for atom in atoms
        ]

    def apply_and_persist(
        self,
        atoms: list[MemoryAtom],
        store: MemoryStore,
        retrieval_counts: dict[str, int] | None = None,
    ) -> list[ConfidenceAdjustment]:
        """Compute adjusted confidence AND persist updated atoms to the store.

        Only updates atoms whose confidence changed by ≥2%.
        """
        adjustments = self.compute_batch(atoms, store, retrieval_counts)
        updated = 0
        for adj in adjustments:
            if abs(adj.new_confidence - adj.old_confidence) >= 0.02:
                atom = store.get_atom(adj.atom_id)
                if atom:
                    updated_atom = atom.model_copy(update={
                        "confidence": adj.new_confidence,
                        "metadata": {
                            **atom.metadata,
                            "confidence_factors": adj.factors,
                            "confidence_adjusted_at": datetime.now(timezone.utc).isoformat(),
                        },
                    })
                    store.upsert_atom(updated_atom)
                    updated += 1
        return adjustments

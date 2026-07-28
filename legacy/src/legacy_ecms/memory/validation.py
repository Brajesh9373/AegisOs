"""Semantic validation — classifies new atoms against existing knowledge.

Upgrades the binary duplicate/contradiction detection into a rich
classification system that determines whether a candidate atom is:
  - a duplicate (identical, should be skipped)
  - a refinement (more detailed version of existing — merge evidence)
  - an extension (adds new information to an existing topic — link as RELATED_TO)
  - a contradiction (direct conflict — mark with CONTRADICTS relationship)
  - a replacement (supersedes existing — preserve history, mark old as superseded)
  - a specialization (narrower version of existing — link as PART_OF)
  - independent knowledge (no relationship — create as new)

Every decision is explainable — the result includes the reasoning.
"""

from __future__ import annotations

import difflib
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from legacy_ecms.memory.domain import (
    MemoryAtom,
    MemoryStatus,
    MemoryType,
    RelatedAtom,
    RelationshipType,
)
from legacy_ecms.memory.interfaces import MemoryStore


class SemanticAction(str, Enum):
    """Classification of a candidate atom relative to existing knowledge."""

    CREATE = "create"
    REFINE = "refine"
    EXTEND = "extend"
    CONTRADICT = "contradict"
    REPLACE = "replace"
    SPECIALIZE = "specialize"
    DUPLICATE = "duplicate"


@dataclass
class SemanticResult:
    """Rich validation result with explainable classification."""

    action: SemanticAction = SemanticAction.CREATE
    related_atom: MemoryAtom | None = None
    similarity: float = 0.0
    reasoning: str = ""
    resolved_atom: MemoryAtom | None = None
    messages: list[str] = field(default_factory=list)

    def explain(self) -> str:
        if self.action == SemanticAction.CREATE:
            return "No similar existing atom found — creating as new knowledge."
        if self.action == SemanticAction.DUPLICATE:
            return f"Near-identical to {self.related_atom.id} (similarity={self.similarity:.0%}). Skipping."
        if self.action == SemanticAction.REFINE:
            return f"Refinement of {self.related_atom.id} (similarity={self.similarity:.0%}). Merging evidence and updating."
        if self.action == SemanticAction.EXTEND:
            return f"Extension of topic '{self.related_atom.topic}' — adding related knowledge atom."
        if self.action == SemanticAction.CONTRADICT:
            return f"Contradicts {self.related_atom.id}. Creating with CONTRADICTS relationship."
        if self.action == SemanticAction.REPLACE:
            return f"Supersedes {self.related_atom.id} (similarity={self.similarity:.0%}). Preserving history."
        if self.action == SemanticAction.SPECIALIZE:
            return f"Specialization of {self.related_atom.id} — linking as PART_OF."
        return self.action.value


class SemanticValidator:
    """Validates a candidate atom against the entire store using multi-factor
    classification instead of simple duplicate/contradiction checks.
    """

    def __init__(
        self,
        store: MemoryStore,
        *,
        duplicate_threshold: float = 0.90,
        refine_threshold: float = 0.75,
        extend_threshold: float = 0.55,
        specialize_threshold: float = 0.50,
    ) -> None:
        self.store = store
        self.duplicate_threshold = duplicate_threshold
        self.refine_threshold = refine_threshold
        self.extend_threshold = extend_threshold
        self.specialize_threshold = specialize_threshold

        # Antonym pairs for contradiction detection
        self._contradiction_pairs: list[tuple[str, str]] = [
            ("always", "never"), ("enabled", "disabled"), ("supported", "unsupported"),
            ("synchronous", "asynchronous"), ("blocking", "non-blocking"),
            ("jwt", "oauth"), ("rest", "graphql"), ("postgres", "mysql"),
            ("sync", "async"), ("deprecated", "recommended"),
        ]

    async def validate(self, candidate: MemoryAtom) -> SemanticResult:
        """Classify candidate against existing atoms and return actionable result."""
        existing = self.store.list_all(limit=200)
        result = SemanticResult()

        best_match: tuple[MemoryAtom | None, float] = (None, 0.0)
        best_action = SemanticAction.CREATE

        for atom in existing:
            if atom.id == candidate.id:
                continue
            if atom.status == MemoryStatus.SUPERSEDED:
                continue

            sim = self._topic_summary_similarity(candidate, atom)

            if sim >= self.duplicate_threshold:
                # Near-identical content — duplicate
                best_match = (atom, sim)
                best_action = SemanticAction.DUPLICATE
                break

            if sim >= self.refine_threshold:
                # Same topic, similar content — could be refinement
                if self._is_same_topic(candidate, atom):
                    if self._candidate_adds_detail(candidate, atom):
                        best_match = (atom, sim)
                        best_action = SemanticAction.REFINE
                        break
                    else:
                        best_match = (atom, sim)
                        best_action = SemanticAction.REPLACE
                        break

            if sim >= self.extend_threshold:
                # Related topic — could be extension
                if self._is_same_topic(candidate, atom) and best_action == SemanticAction.CREATE:
                    best_match = (atom, sim)
                    best_action = SemanticAction.EXTEND

            if sim >= self.specialize_threshold:
                # One topic is a substring of the other — specialization
                if (candidate.topic.lower() in atom.topic.lower() or
                    atom.topic.lower() in candidate.topic.lower()):
                    if best_action == SemanticAction.CREATE:
                        best_match = (atom, sim)
                        best_action = SemanticAction.SPECIALIZE

            # Contradiction check
            if self._detect_contradiction(candidate, atom) and best_action == SemanticAction.CREATE:
                best_match = (atom, sim)
                best_action = SemanticAction.CONTRADICT

        result.related_atom = best_match[0]
        result.similarity = best_match[1]
        result.action = best_action

        # Build resolved atom per action
        result = self._apply_action(candidate, result)
        return result

    # ── Similarity ──────────────────────────────────────────────────

    def _topic_summary_similarity(self, a: MemoryAtom, b: MemoryAtom) -> float:
        """Sequence matcher over topic + summary."""
        text_a = f"{a.topic} {a.summary}".lower()
        text_b = f"{b.topic} {b.summary}".lower()
        return difflib.SequenceMatcher(None, text_a, text_b).ratio()

    def _is_same_topic(self, a: MemoryAtom, b: MemoryAtom) -> bool:
        """Check if two atoms share the same topic domain."""
        a_prefix = a.topic.split(":")[0].strip().lower()
        b_prefix = b.topic.split(":")[0].strip().lower()
        a_words = set(a.topic.lower().split()) - {"is", "the", "a", "an"}
        b_words = set(b.topic.lower().split()) - {"is", "the", "a", "an"}
        overlap = a_words & b_words
        return a_prefix == b_prefix or len(overlap) >= 2

    def _candidate_adds_detail(self, candidate: MemoryAtom, existing: MemoryAtom) -> bool:
        """Check if candidate provides more detail than existing (longer summary
        and same or higher confidence)."""
        return len(candidate.summary) > len(existing.summary) * 1.2

    # ── Contradiction ───────────────────────────────────────────────

    def _detect_contradiction(self, a: MemoryAtom, b: MemoryAtom) -> bool:
        """Detect contradictions via antonym pairs."""
        a_lower = f"{a.topic} {a.summary}".lower()
        b_lower = f"{b.topic} {b.summary}".lower()
        for a_word, b_word in self._contradiction_pairs:
            if a_word in a_lower and b_word in b_lower and a_word not in b_lower:
                return True
            if b_word in a_lower and a_word in b_lower and b_word not in b_lower:
                return True
        return False

    # ── Apply Action ────────────────────────────────────────────────

    def _apply_action(self, candidate: MemoryAtom, result: SemanticResult) -> SemanticResult:
        """Mutate the store and set resolved_atom based on the classification."""
        existing = result.related_atom

        if result.action == SemanticAction.CREATE:
            result.resolved_atom = candidate

        elif result.action == SemanticAction.DUPLICATE:
            result.resolved_atom = None  # skip — no persistence
            result.messages.append(f"Duplicate of {existing.id if existing else '?'}")

        elif result.action == SemanticAction.REFINE:
            merged_evidence = list(set(
                [e.model_dump() for e in candidate.evidence] +
                [e.model_dump() for e in (existing.evidence if existing else [])]
            ))
            from legacy_ecms.memory.domain import Evidence
            resolved = candidate.model_copy(update={
                "id": existing.id if existing else candidate.id,
                "version": (existing.version + 1) if existing else 1,
                "version_history": [*(existing.version_history if existing else []),
                                    existing.model_dump()] if existing else [],
                "confidence": max(candidate.confidence, existing.confidence if existing else 0),
                "evidence": [Evidence(**e) for e in merged_evidence],
                "validated_at": candidate.validated_at or (
                    existing.validated_at if existing else None
                ),
                "related_atoms": list(set(
                    (candidate.related_atoms or []) + (existing.related_atoms if existing else [])
                )),
            })
            if existing:
                self.store.supersede_atom(existing.id, resolved.id)
            result.resolved_atom = resolved
            result.messages.append(f"Refined {existing.id if existing else '?'}")

        elif result.action == SemanticAction.EXTEND:
            result.resolved_atom = candidate.model_copy(update={
                "related_atoms": [
                    *(candidate.related_atoms or []),
                    RelatedAtom(
                        atom_id=existing.id,
                        type=RelationshipType.RELATED_TO,
                        confidence=result.similarity,
                    ) if existing else None,
                ],
            })
            result.messages.append(f"Extension of {existing.id if existing else '?'}")

        elif result.action == SemanticAction.CONTRADICT:
            result.resolved_atom = candidate.model_copy(update={
                "status": MemoryStatus.DRAFT,
                "confidence": min(candidate.confidence, 0.60),
                "related_atoms": [
                    *(candidate.related_atoms or []),
                    RelatedAtom(
                        atom_id=existing.id,
                        type=RelationshipType.CONTRADICTS,
                        confidence=0.80,
                    ) if existing else None,
                ],
            })
            result.messages.append(f"Contradicts {existing.id if existing else '?'}")

        elif result.action == SemanticAction.REPLACE:
            resolved = candidate.model_copy(update={
                "version": (existing.version + 1) if existing else 1,
                "version_history": [*(existing.version_history if existing else []),
                                    existing.model_dump()] if existing else [],
            })
            if existing:
                self.store.supersede_atom(existing.id, resolved.id)
            result.resolved_atom = resolved
            result.messages.append(f"Replaces {existing.id if existing else '?'}")

        elif result.action == SemanticAction.SPECIALIZE:
            result.resolved_atom = candidate.model_copy(update={
                "related_atoms": [
                    *(candidate.related_atoms or []),
                    RelatedAtom(
                        atom_id=existing.id,
                        type=RelationshipType.PART_OF,
                        confidence=result.similarity,
                    ) if existing else None,
                ],
            })
            result.messages.append(f"Specialization of {existing.id if existing else '?'}")

        return result

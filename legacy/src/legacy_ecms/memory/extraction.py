"""Conversation memory extraction — parses a Q&A pair into multiple typed atoms.

Replaces the previous single-atom-per-conversation approach. A single
conversation may contain facts, architecture, decisions, trade-offs, bugs,
etc. The extractor identifies these categories and creates one atom per
distinct knowledge unit.

Then runs each candidate through the SemanticValidator (classifies as
duplicate/refinement/extension/contradiction/replacement/specialization)
and persists only valid atoms.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from legacy_ecms.memory.domain import (
    Evidence,
    EvidenceSource,
    MemoryAtom,
    MemoryScope,
    MemoryStatus,
    MemoryType,
    RelatedAtom,
    RelationshipType,
)
from legacy_ecms.memory.interfaces import MemoryStore
from legacy_ecms.memory.validation import SemanticValidator, SemanticAction


# ── Extraction patterns ─────────────────────────────────────────────

# Each pattern maps a content signal to a MemoryType.
# Signals are keyword-based. For production, replace with LLM-based extraction.
EXTRACTION_PATTERNS: list[tuple[MemoryType, list[str]]] = [
    (MemoryType.FACT, ["is", "are", "uses", "contains", "runs on", "connects to", "supports", "implements"]),
    (MemoryType.ARCHITECTURE, ["architecture", "layer", "component", "module", "service", "microservice", "monolith", "pipeline"]),
    (MemoryType.DECISION, ["decided", "chose", "selected", "picked", "opted", "went with", "adopted"]),
    (MemoryType.CONVENTION, ["convention", "standard", "pattern", "always do", "best practice is", "we always"]),
    (MemoryType.BUG, ["bug", "issue", "broken", "doesn't work", "fails", "error", "crash", "race condition"]),
    (MemoryType.LIMITATION, ["can't", "cannot", "doesn't support", "not supported", "limitation", "caveat", "unable"]),
    (MemoryType.TRADE_OFF, ["trade-off", "tradeoff", "pros and cons", "downside", "advantage", "disadvantage"]),
    (MemoryType.PERFORMANCE, ["slow", "fast", "latency", "throughput", "bottleneck", "scales", "performance", "benchmark"]),
    (MemoryType.SECURITY, ["vulnerability", "CVE", "exploit", "injection", "XSS", "CSRF", "authentication bypass", "unauthorized"]),
    (MemoryType.DESIGN_RATIONALE, ["because", "reason", "rationale", "motivation", "why we", "background"]),
    (MemoryType.BEST_PRACTICE, ["best practice", "recommended", "should always", "prefer", "idiomatic"]),
    (MemoryType.KNOWN_RISK, ["risk", "could break", "might fail", "fragile", "brittle", "depends on external"]),
]


class ExtractionResult:
    """Result of extracting atoms from a Q&A pair."""

    def __init__(self) -> None:
        self.candidates: list[MemoryAtom] = []
        self.validated_count: int = 0
        self.created_count: int = 0
        self.merged_count: int = 0
        self.superseded_count: int = 0
        self.draft_count: int = 0
        self.rejected_count: int = 0


class ConversationExtractor:
    """Extracts multiple typed memory atoms from a single Q&A pair.

    Usage:
        extractor = ConversationExtractor(store)
        result = await extractor.extract_and_persist(
            question="How does auth work?",
            answer="JWT tokens expire after 1 hour...",
            session_id="abc-123",
        )
        # result.created_count = 3  (three distinct atoms created)
    """

    def __init__(
        self,
        store: MemoryStore,
        min_confidence: float = 0.70,
        max_atoms_per_conversation: int = 8,
    ) -> None:
        self.store = store
        self.min_confidence = min_confidence
        self.max_atoms = max_atoms_per_conversation
        self.validator = SemanticValidator(store)

    async def extract_and_persist(
        self,
        question: str,
        answer: str,
        session_id: str,
        workspace_id: str = "default",
    ) -> ExtractionResult:
        """Full extraction pipeline: parse → classify → validate → persist."""
        result = ExtractionResult()

        # Step 1 — Split answer into sentences/phrases
        segments = self._segment(answer)

        # Step 2 — Classify each segment into one or more MemoryTypes
        for segment in segments[:self.max_atoms * 3]:  # generous pre-filter
            types = self._classify(segment)
            if not types:
                continue

            for mtype in types[:1]:  # assign primary type per segment
                topic = self._infer_topic(segment, question, mtype)
                summary = segment[:400]

                atom = MemoryAtom(
                    id=MemoryAtom.generate_id(topic, 0),  # temp ID, replaced by validation
                    type=mtype,
                    topic=topic,
                    summary=summary,
                    confidence=0.80,
                    status=MemoryStatus.DRAFT,
                    scope=MemoryScope.WORKSPACE,
                    evidence=[
                        Evidence(
                            source=f"session:{session_id}",
                            source_type=EvidenceSource.CONVERSATION,
                            description=f"Extracted from Q&A on {datetime.now(timezone.utc).isoformat()[:10]}",
                        )
                    ],
                    tags=["conversation", topic.lower().replace(" ", "-")[:30]],
                    validated_at=None,
                )
                result.candidates.append(atom)

                if len(result.candidates) >= self.max_atoms:
                    break

        # Step 3 — Semantic validation: classify each candidate against existing atoms
        validated_atoms: list[MemoryAtom] = []
        for candidate in result.candidates:
            validation = await self.validator.validate(candidate)
            if validation.action == SemanticAction.DUPLICATE:
                result.rejected_count += 1
                continue
            if validation.resolved_atom is None:
                result.rejected_count += 1
                continue

            resolved = validation.resolved_atom.model_copy(update={
                "id": self._unique_id(candidate.topic, result.created_count + 1),
            })

            if validation.action == SemanticAction.CREATE:
                result.created_count += 1
            elif validation.action == SemanticAction.REFINE:
                result.merged_count += 1
            elif validation.action == SemanticAction.EXTEND:
                result.created_count += 1
            elif validation.action == SemanticAction.CONTRADICT:
                result.draft_count += 1
            elif validation.action == SemanticAction.REPLACE:
                result.superseded_count += 1
            elif validation.action == SemanticAction.SPECIALIZE:
                result.created_count += 1
            else:
                result.created_count += 1

            validated_atoms.append(resolved)

        # Step 4 — Persist validated atoms
        for atom in validated_atoms:
            self.store.upsert_atom(atom)
            result.validated_count += 1

        return result

    # ── Helpers ─────────────────────────────────────────────────────

    def _segment(self, text: str) -> list[str]:
        """Split text into distinct knowledge segments.

        Uses sentence boundaries (period, newline, semicolon) and
        heading markers. Returns segments of at least 30 chars.
        """
        import re
        # Split on sentence boundaries and markdown headings
        raw = re.split(r"(?<=[.!?])\s+|(?<=\n)\s*(?=#)|(?<=\n\n)|(?<=;)\s+", text)
        segments: list[str] = []
        for r in raw:
            r = r.strip()
            if len(r) < 30:
                # Append to previous segment if too short
                if segments and len(segments[-1]) + len(r) < 500:
                    segments[-1] = segments[-1] + " " + r
                elif len(r) > 10:
                    segments.append(r)
                continue
            segments.append(r)
        return segments

    def _classify(self, text: str) -> list[MemoryType]:
        """Classify a text segment into MemoryType(s) by keyword matching."""
        text_lower = text.lower()
        matched: list[tuple[int, MemoryType]] = []
        for mtype, signals in EXTRACTION_PATTERNS:
            score = sum(1 for s in signals if s in text_lower)
            if score > 0:
                matched.append((score, mtype))
        matched.sort(key=lambda x: -x[0])
        # Return all types with matching signals
        return [m for _, m in matched[:2]]

    def _infer_topic(self, segment: str, question: str, mtype: MemoryType) -> str:
        """Infer a short topic from the segment and original question."""
        # Use the first sentence as topic, capped at 80 chars
        first_sentence = segment.split(".")[0].strip()
        if len(first_sentence) > 80:
            # Truncate to the last complete word under 80 chars
            words = first_sentence[:80].split()
            topic = " ".join(words[:-1]) if len(words) > 3 else words[0]
        else:
            topic = first_sentence

        # Prefix with type for readability
        type_prefix = mtype.value.replace("_", " ").title()
        return f"{type_prefix}: {topic[:70]}"

    def _unique_id(self, topic: str, counter: int) -> str:
        """Generate a unique atom ID."""
        import uuid
        short = uuid.uuid4().hex[:6].upper()
        prefix = topic.replace(" ", "-").replace(":", "").upper()[:6]
        return f"{prefix}-{short}"

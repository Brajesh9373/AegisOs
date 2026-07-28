"""Provenance tracking — attaches evidence citations to every agent response.

After every Q&A turn, the agent's answer is analyzed for statements that
can be traced back to source memory atoms, files, or conversations. The
backend stores these provenance mappings so future UI features can show
"why was this answer given?" and "which memories influenced this answer?"

Provenance is backend-only — no UI implementation here, but the data
structure supports eventual citation rendering.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from legacy_ecms.memory.domain import MemoryAtom, ScoredAtom
from legacy_ecms.memory.interfaces import MemoryStore


@dataclass
class StatementProvenance:
    """Maps a single statement/fact in the agent's response back to its sources."""

    statement: str
    atom_ids: list[str] = field(default_factory=list)
    atom_topics: list[str] = field(default_factory=list)
    confidence: float = 0.0
    source: str = "unknown"  # memory | inspection | user | general

    @property
    def atom_count(self) -> int:
        return len(self.atom_ids)


@dataclass
class ResponseProvenance:
    """Full provenance for a complete agent response."""

    session_id: str
    question: str
    answer: str
    statements: list[StatementProvenance] = field(default_factory=list)
    primary_atoms_used: list[str] = field(default_factory=list)
    supporting_atoms_used: list[str] = field(default_factory=list)
    graph_nodes_referenced: int = 0
    total_citations: int = 0

    def summary(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "statements_tracked": len(self.statements),
            "statements_with_citations": sum(1 for s in self.statements if s.atom_ids),
            "primary_atoms_used": len(self.primary_atoms_used),
            "supporting_atoms_used": len(self.supporting_atoms_used),
            "graph_nodes_referenced": self.graph_nodes_referenced,
            "total_citations": self.total_citations,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "question": self.question[:200],
            "answer_preview": self.answer[:200],
            "statements": [
                {
                    "statement": s.statement[:200],
                    "atom_ids": s.atom_ids,
                    "atom_topics": s.atom_topics,
                    "confidence": s.confidence,
                    "source": s.source,
                }
                for s in self.statements
            ],
            "primary_atoms_used": self.primary_atoms_used,
            "supporting_atoms_used": self.supporting_atoms_used,
            "total_citations": self.total_citations,
        }


class ProvenanceTracker:
    """Analyzes agent responses and maps statements back to source memory atoms.

    Works by:
      1. Splitting the response into sentences/statements
      2. For each statement, checking if it references a known atom ID or topic
      3. Matching keywords in the statement against atom summaries
      4. Building a ResponseProvenance with full citation chains

    The resulting provenance can be stored alongside the response and used
    by future UI features to show evidence citations.
    """

    def __init__(self, store: MemoryStore) -> None:
        self.store = store

    def track(
        self,
        session_id: str,
        question: str,
        answer: str,
        retrieved_atoms: list[ScoredAtom] | None = None,
    ) -> ResponseProvenance:
        """Analyze an answer and build provenance mappings.

        Args:
            session_id: The ECMS session ID.
            question: The user's original question.
            answer: The agent's full response text.
            retrieved_atoms: The atoms used as context for this response.

        Returns:
            ResponseProvenance with statement-to-source mappings.
        """
        prov = ResponseProvenance(
            session_id=session_id,
            question=question,
            answer=answer,
        )

        atoms = retrieved_atoms or []
        prov.primary_atoms_used = [sc.atom.id for sc in atoms[:5]]
        prov.supporting_atoms_used = [sc.atom.id for sc in atoms[5:]]

        # Build lookup: atom_id → atom, and topic → atom
        atom_lookup: dict[str, MemoryAtom] = {}
        topic_lookup: dict[str, list[MemoryAtom]] = {}
        for sc in atoms:
            a = sc.atom
            atom_lookup[a.id] = a
            topic_lookup.setdefault(a.topic.lower(), []).append(a)

        # Split answer into sentences
        statements = self._split_sentences(answer)

        total_citations = 0
        for stmt_text in statements:
            stmt_prov = StatementProvenance(statement=stmt_text)

            # 1. Direct atom ID references (e.g., "AUTH-001")
            atom_refs = re.findall(r"\b([A-Z]+-\d{3})\b", stmt_text)
            for ref in atom_refs:
                if ref in atom_lookup:
                    stmt_prov.atom_ids.append(ref)
                    stmt_prov.atom_topics.append(atom_lookup[ref].topic)
                    total_citations += 1

            # 2. Topic keyword matching
            if not stmt_prov.atom_ids:
                stmt_lower = stmt_text.lower()
                for topic, topic_atoms in topic_lookup.items():
                    # Check if ≥2 topic words appear in the statement
                    topic_words = set(topic.lower().split())
                    match_count = sum(1 for w in topic_words if len(w) > 3 and w in stmt_lower)
                    if match_count >= 2:
                        for ta in topic_atoms[:1]:  # one atom per topic
                            if ta.id not in stmt_prov.atom_ids:
                                stmt_prov.atom_ids.append(ta.id)
                                stmt_prov.atom_topics.append(ta.topic)
                                total_citations += 1

            # 3. Determine source
            if stmt_prov.atom_ids:
                stmt_prov.source = "memory"
                confidences = [
                    atom_lookup[aid].confidence
                    for aid in stmt_prov.atom_ids
                    if aid in atom_lookup
                ]
                stmt_prov.confidence = (
                    sum(confidences) / len(confidences) if confidences else 0.0
                )
            elif any(
                kw in stmt_text.lower()
                for kw in ["file", "code", "inspect", "found", "directory"]
            ):
                stmt_prov.source = "inspection"
            elif any(
                kw in stmt_text.lower()
                for kw in ["you said", "you asked", "your question"]
            ):
                stmt_prov.source = "user"
            else:
                stmt_prov.source = "general"

            prov.statements.append(stmt_prov)

        prov.graph_nodes_referenced = len({
            aid for s in prov.statements for aid in s.atom_ids
        })
        prov.total_citations = total_citations
        return prov

    def _split_sentences(self, text: str) -> list[str]:
        """Split text into sentences, merging very short fragments."""
        raw = re.split(r"(?<=[.!?])\s+|\n\n", text)
        sentences: list[str] = []
        for r in raw:
            r = r.strip()
            if not r:
                continue
            if len(r) < 25 and sentences:
                sentences[-1] = sentences[-1] + " " + r
            else:
                sentences.append(r)
        return sentences

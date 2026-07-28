"""Automatic relationship discovery from memory atoms, tags, evidence, and content.

Each extractor is an independent strategy that examines the current atom store
and produces relationship candidates. The pipeline composes extractors without
knowing their internal logic.

All extractors operate on the MemoryStore protocol — storage-agnostic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from legacy_ecms.memory.domain import (
    MemoryAtom,
    MemoryRelationship,
    MemoryType,
    RelationshipType,
)
from legacy_ecms.memory.interfaces import MemoryStore


# ── Discovery Result ────────────────────────────────────────────────

class RelationshipCandidate:
    """A proposed relationship with confidence and evidence."""

    def __init__(
        self,
        source_id: str,
        target_id: str,
        rel_type: RelationshipType,
        confidence: float,
        evidence: list[str],
        method: str,
    ) -> None:
        self.source_id = source_id
        self.target_id = target_id
        self.rel_type = rel_type
        self.confidence = min(1.0, max(0.0, confidence))
        self.evidence = evidence
        self.method = method


# ── Extractor Protocol ──────────────────────────────────────────────

class RelationshipExtractor(ABC):
    """Abstract relationship extractor — pluggable into the discovery pipeline."""

    name: str = "base"

    @abstractmethod
    def extract(self, store: MemoryStore) -> list[RelationshipCandidate]:
        """Analyze all atoms in the store and return candidate relationships."""
        ...


# ── Tag-Based Extractor ─────────────────────────────────────────────

class TagOverlapExtractor(RelationshipExtractor):
    """If two atoms share tags, they are RELATED_TO.

    Stronger signal (higher confidence) if they also share topics.
    """

    name = "tag_overlap"

    NEW_REL = RelationshipType.RELATED_TO

    def extract(self, store: MemoryStore) -> list[RelationshipCandidate]:
        atoms = store.list_all(limit=500)
        candidates: list[RelationshipCandidate] = []
        seen_pairs: set[tuple[str, str]] = set()

        for i, a1 in enumerate(atoms):
            for a2 in atoms[i + 1 :]:
                pair = (a1.id, a2.id)
                if pair in seen_pairs or (a2.id, a1.id) in seen_pairs:
                    continue
                seen_pairs.add(pair)

                t1 = set(a1.tags)
                t2 = set(a2.tags)
                overlap = t1 & t2
                if not overlap:
                    continue

                # Score: more shared tags → higher confidence
                jaccard = len(overlap) / len(t1 | t2) if (t1 | t2) else 0
                # Boost if topics overlap too
                topic_overlap = bool(set(a1.topic.lower().split()) & set(a2.topic.lower().split()))
                confidence = min(1.0, jaccard * 0.7 + (0.2 if topic_overlap else 0) + 0.1)

                candidates.append(RelationshipCandidate(
                    source_id=a1.id,
                    target_id=a2.id,
                    rel_type=RelationshipType.RELATED_TO,
                    confidence=confidence,
                    evidence=[f"tag-overlap: {', '.join(overlap)}"],
                    method="tag_overlap",
                ))
        return candidates


# ── Evidence-Based Extractor ─────────────────────────────────────────

class SharedEvidenceExtractor(RelationshipExtractor):
    """If two atoms cite the same evidence source, they are RELATED_TO.

    If one atom's evidence is a prefix of another's, it's a DERIVED_FROM.
    """

    name = "shared_evidence"

    def extract(self, store: MemoryStore) -> list[RelationshipCandidate]:
        atoms = store.list_all(limit=500)
        candidates: list[RelationshipCandidate] = []
        seen_pairs: set[tuple[str, str]] = set()

        for i, a1 in enumerate(atoms):
            e1_sources = {e.source for e in a1.evidence}
            if not e1_sources:
                continue
            for a2 in atoms[i + 1 :]:
                pair = (a1.id, a2.id)
                if pair in seen_pairs or (a2.id, a1.id) in seen_pairs:
                    continue
                seen_pairs.add(pair)

                e2_sources = {e.source for e in a2.evidence}
                shared = e1_sources & e2_sources
                if not shared:
                    continue

                # Check for prefix relationship (DERIVED_FROM)
                is_derived = False
                for s1 in e1_sources:
                    for s2 in e2_sources:
                        if s1.startswith(s2) or s2.startswith(s1):
                            is_derived = True
                            break

                rel_type = RelationshipType.DERIVED_FROM if is_derived else RelationshipType.REFERENCES
                confidence = min(1.0, 0.6 + len(shared) * 0.2)

                candidates.append(RelationshipCandidate(
                    source_id=a1.id,
                    target_id=a2.id,
                    rel_type=rel_type,
                    confidence=confidence,
                    evidence=[f"shared-evidence: {', '.join(list(shared)[:3])}"],
                    method="shared_evidence",
                ))
        return candidates


# ── Topic Hierarchy Extractor ────────────────────────────────────────

class TopicHierarchyExtractor(RelationshipExtractor):
    """If atom B's topic is a substring of atom A's topic, B is PART_OF A.

    Example: "Authentication: JWT" is PART_OF "Authentication: Services"
    if the latter is broader. Also handles category-based grouping
    (e.g., same topic prefix → RELATED_TO).
    """

    name = "topic_hierarchy"

    def extract(self, store: MemoryStore) -> list[RelationshipCandidate]:
        atoms = store.list_all(limit=500)
        candidates: list[RelationshipCandidate] = []
        seen_pairs: set[tuple[str, str]] = set()

        for i, a1 in enumerate(atoms):
            t1 = a1.topic.lower()
            for a2 in atoms[i + 1 :]:
                pair = (a1.id, a2.id)
                if pair in seen_pairs or (a2.id, a1.id) in seen_pairs:
                    continue
                seen_pairs.add(pair)

                t2 = a2.topic.lower()

                # Check if one topic is a substring of the other
                if t1 in t2 or t2 in t1:
                    # The shorter topic is the broader category → PART_OF
                    if len(t1) < len(t2):
                        broader, narrower = a1, a2
                    else:
                        broader, narrower = a2, a1

                    confidence = 0.85 if ":" in broader.topic or ":" in narrower.topic else 0.75
                    candidates.append(RelationshipCandidate(
                        source_id=narrower.id,
                        target_id=broader.id,
                        rel_type=RelationshipType.PART_OF,
                        confidence=confidence,
                        evidence=[f"topic-hierarchy: {broader.topic} ⊃ {narrower.topic}"],
                        method="topic_hierarchy",
                    ))

                # Same topic prefix (before ":") → RELATED_TO sibling
                t1_prefix = t1.split(":")[0].strip()
                t2_prefix = t2.split(":")[0].strip()
                if t1_prefix == t2_prefix and t1_prefix:
                    candidates.append(RelationshipCandidate(
                        source_id=a1.id,
                        target_id=a2.id,
                        rel_type=RelationshipType.RELATED_TO,
                        confidence=0.70,
                        evidence=[f"topic-sibling: {t1_prefix}"],
                        method="topic_hierarchy",
                    ))

        return candidates


# ── Type-Based Extractor ─────────────────────────────────────────────

class TypePatternExtractor(RelationshipExtractor):
    """Infer domain-specific relationships from type combinations.

    - FACT + ARCHITECTURE both referencing a topic → FACT::IMPLEMENTS::ARCHITECTURE
    - DECISION + ARCHITECTURE on same topic → DECISION::AFFECTS::ARCHITECTURE
    - RESOLUTION + BUG → RESOLUTION::RESOLVES::BUG
    - HYPOTHESIS → FACT on same topic → HYPOTHESIS::DERIVED_FROM::FACT
    """

    name = "type_pattern"

    PATTERNS: list[tuple[set[MemoryType], set[MemoryType], RelationshipType, float, str]] = [
        ({MemoryType.FACT}, {MemoryType.ARCHITECTURE}, RelationshipType.IMPLEMENTS, 0.78, "fact-implements-arch"),
        ({MemoryType.DECISION}, {MemoryType.ARCHITECTURE}, RelationshipType.AFFECTS, 0.82, "decision-affects-arch"),
        ({MemoryType.RESOLUTION}, {MemoryType.BUG}, RelationshipType.RESOLVES, 0.90, "resolution-resolves-bug"),
        ({MemoryType.HYPOTHESIS}, {MemoryType.FACT}, RelationshipType.DERIVED_FROM, 0.72, "hypothesis-derived-from-fact"),
        ({MemoryType.BEST_PRACTICE}, {MemoryType.CONVENTION}, RelationshipType.DERIVED_FROM, 0.75, "best-practice-derived-from-convention"),
        ({MemoryType.PERFORMANCE}, {MemoryType.ARCHITECTURE}, RelationshipType.AFFECTS, 0.70, "performance-affects-arch"),
        ({MemoryType.SECURITY}, {MemoryType.ARCHITECTURE}, RelationshipType.AFFECTS, 0.80, "security-affects-arch"),
    ]

    def extract(self, store: MemoryStore) -> list[RelationshipCandidate]:
        atoms = store.list_all(limit=500)
        candidates: list[RelationshipCandidate] = []
        seen_pairs: set[tuple[str, str]] = set()

        for i, a1 in enumerate(atoms):
            for a2 in atoms[i + 1 :]:
                pair = (a1.id, a2.id)
                if pair in seen_pairs or (a2.id, a1.id) in seen_pairs:
                    continue
                seen_pairs.add(pair)

                for src_types, tgt_types, rel_type, confidence, pattern_name in self.PATTERNS:
                    # Check both directions
                    if a1.type in src_types and a2.type in tgt_types:
                        candidates.append(RelationshipCandidate(
                            source_id=a1.id, target_id=a2.id,
                            rel_type=rel_type, confidence=confidence,
                            evidence=[f"type-pattern: {pattern_name}"],
                            method="type_pattern",
                        ))
                    elif a2.type in src_types and a1.type in tgt_types:
                        candidates.append(RelationshipCandidate(
                            source_id=a2.id, target_id=a1.id,
                            rel_type=rel_type, confidence=confidence,
                            evidence=[f"type-pattern: {pattern_name}"],
                            method="type_pattern",
                        ))
        return candidates


# ── Semantic Similarity Extractor ────────────────────────────────────

class SemanticSimilarityExtractor(RelationshipExtractor):
    """If two atoms have high summary semantic similarity, they are RELATED_TO.

    Uses simple token overlap as a cheap proxy. For production, replace
    with embedding-based cosine similarity.
    """

    name = "semantic_similarity"

    def __init__(self, threshold: float = 0.55) -> None:
        self.threshold = threshold

    def extract(self, store: MemoryStore) -> list[RelationshipCandidate]:
        import difflib

        atoms = store.list_all(limit=500)
        candidates: list[RelationshipCandidate] = []
        seen_pairs: set[tuple[str, str]] = set()

        for i, a1 in enumerate(atoms):
            s1 = f"{a1.topic} {a1.summary}".lower()
            for a2 in atoms[i + 1 :]:
                pair = (a1.id, a2.id)
                if pair in seen_pairs or (a2.id, a1.id) in seen_pairs:
                    continue
                seen_pairs.add(pair)

                s2 = f"{a2.topic} {a2.summary}".lower()
                sim = difflib.SequenceMatcher(None, s1, s2).ratio()
                if sim >= self.threshold:
                    candidates.append(RelationshipCandidate(
                        source_id=a1.id, target_id=a2.id,
                        rel_type=RelationshipType.RELATED_TO,
                        confidence=min(1.0, sim),
                        evidence=[f"semantic-similarity: {sim:.0%}"],
                        method="semantic_similarity",
                    ))
        return candidates


# ── Discovery Pipeline ───────────────────────────────────────────────

class RelationshipDiscoveryPipeline:
    """Composable pipeline for automatic relationship discovery.

    Each extractor runs independently and produces candidates. The pipeline
    deduplicates, merges, and persists them into the store.

    Usage:
        pipeline = RelationshipDiscoveryPipeline(store)
        pipeline.add_extractor(TagOverlapExtractor())
        pipeline.add_extractor(SharedEvidenceExtractor())
        pipeline.add_extractor(TopicHierarchyExtractor())
        pipeline.add_extractor(TypePatternExtractor())
        result = pipeline.discover()
    """

    def __init__(self, store: MemoryStore) -> None:
        self.store = store
        self._extractors: list[RelationshipExtractor] = []

    def add_extractor(self, extractor: RelationshipExtractor) -> "RelationshipDiscoveryPipeline":
        self._extractors.append(extractor)
        return self

    @classmethod
    def default_pipeline(cls, store: MemoryStore) -> "RelationshipDiscoveryPipeline":
        return (
            cls(store)
            .add_extractor(TagOverlapExtractor())
            .add_extractor(SharedEvidenceExtractor())
            .add_extractor(TopicHierarchyExtractor())
            .add_extractor(TypePatternExtractor())
            .add_extractor(SemanticSimilarityExtractor())
        )

    def discover(self, persist: bool = True, min_confidence: float = 0.50) -> list[MemoryRelationship]:
        """Run all extractors, deduplicate, merge, and optionally persist.

        Returns the final deduplicated relationship list.
        """
        all_candidates: list[RelationshipCandidate] = []
        for extractor in self._extractors:
            extracted = extractor.extract(self.store)
            all_candidates.extend(extracted)

        # Deduplicate by (source_id, target_id, rel_type) — keep highest confidence
        merged: dict[tuple[str, str, RelationshipType], MemoryRelationship] = {}
        for cand in all_candidates:
            if cand.confidence < min_confidence:
                continue
            key = (cand.source_id, cand.target_id, cand.rel_type)
            if key in merged:
                existing = merged[key]
                # Merge: average confidence, union evidence
                avg_conf = (existing.confidence + cand.confidence) / 2
                all_evidence = list(set(existing.evidence + cand.evidence))
                merged[key] = MemoryRelationship(
                    id=existing.id,
                    source_id=existing.source_id,
                    target_id=existing.target_id,
                    type=existing.type,
                    confidence=avg_conf,
                    evidence=all_evidence,
                    metadata={"methods": [existing.metadata.get("method"), cand.method]},
                )
            else:
                merged[key] = MemoryRelationship(
                    id=MemoryRelationship.generate_id(),
                    source_id=cand.source_id,
                    target_id=cand.target_id,
                    type=cand.rel_type,
                    confidence=cand.confidence,
                    evidence=cand.evidence,
                    metadata={"method": cand.method},
                )

        relationships = list(merged.values())

        if persist:
            for rel in relationships:
                self.store.upsert_relationship(rel)

        return relationships

    def discover_and_embed(self) -> dict[str, Any]:
        """Run discovery, persist relationships, and embed `related_atoms` references
        directly into each MemoryAtom for retrieval-time traversal.

        Returns a summary of changes.
        """
        relationships = self.discover(persist=True)

        # Build adjacencies
        adj: dict[str, list[tuple[str, RelationshipType, float]]] = {}
        for rel in relationships:
            adj.setdefault(rel.source_id, []).append((rel.target_id, rel.type, rel.confidence))
            adj.setdefault(rel.target_id, []).append((rel.source_id, rel.type, rel.confidence))

        # Embed into atoms
        updated_count = 0
        for atom_id, refs in adj.items():
            atom = self.store.get_atom(atom_id)
            if atom is None:
                continue
            existing_ids = {r.atom_id for r in atom.related_atoms}
            new_refs = [
                r for r in atom.related_atoms
                if r.atom_id in refs
            ]
            for target_id, rel_type, confidence in refs:
                if target_id not in existing_ids:
                    from legacy_ecms.memory.domain import RelatedAtom
                    new_refs.append(RelatedAtom(
                        atom_id=target_id, type=rel_type, confidence=confidence,
                    ))

            if len(new_refs) != len(atom.related_atoms):
                updated = atom.model_copy(update={"related_atoms": new_refs})
                self.store.upsert_atom(updated)
                updated_count += 1

        return {
            "relationships_discovered": len(relationships),
            "atoms_updated": updated_count,
            "extractors_used": [e.name for e in self._extractors],
        }

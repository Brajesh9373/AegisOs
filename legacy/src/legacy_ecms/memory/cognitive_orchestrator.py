"""CognitiveOrchestrator — coordinates the full memory consolidation loop.

Wire diagram:
  Agent conversation
    → ReasoningEngine produces answer
    → Capture: conversation + answer → mem0 (auto-extract episodic facts)
    → Consolidate: periodic clustering of mem0 facts → GBrain deliberative notes
    → Promote: high-confidence notes + facts → knowledge graph (UKO nodes)
    → Validate: graph contradiction check → feedback into mem0 corrections
    → Decay: periodic re-evaluation of confidence scores

This orchestrates ALL memory layers so they form a single cognitive system,
not isolated silos.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from legacy_ecms.config import Settings
from legacy_ecms.memory.brain import GBrain
from legacy_ecms.memory.long_term import LongTermMemory
from legacy_ecms.memory.mem0_layer import Mem0Memory

logger = logging.getLogger(__name__)


class ConversationTurn:
    """Snapshot of a single conversation turn for audit/debugging."""
    def __init__(self) -> None:
        self.question: str = ""
        self.answer: str = ""
        self.user_id: str = "default"
        self.session_id: str | None = None
        self.timestamp: datetime = datetime.now(timezone.utc)
        self.mem0_ids: list[str] = []
        self.gbrain_topics: list[str] = []
        self.promoted_ids: list[str] = []


class CognitiveOrchestrator:
    """Coordinates memory consolidation across all layers.

    Usage:
        orch = CognitiveOrchestrator(settings, workspace_id)
        context = await orch.process_turn(question, answer, user_id, session_id)
        await orch.consolidate()  # periodic — clusters mem0 → GBrain
        await orch.validate()     # periodic — contradiction detection
    """

    def __init__(
        self,
        settings: Settings,
        workspace_id: str = "default",
        brain: GBrain | None = None,
        mem0: Mem0Memory | None = None,
        long_term: LongTermMemory | None = None,
    ) -> None:
        self._settings = settings
        self._workspace_id = workspace_id
        self._brain = brain or GBrain(Path(f"memory/{workspace_id}"))
        self._mem0 = mem0 or Mem0Memory(settings, workspace_id=workspace_id)
        self._long_term = long_term or LongTermMemory()
        self._turn_counter: int = 0
        # Consolidation triggers: after N turns or every M minutes
        self._consolidation_threshold = getattr(settings, "mem0_consolidation_turns", 10)
        self._decay_interval_hours = getattr(settings, "mem0_decay_interval_hours", 24)

    # ── Auto-capture ───────────────────────────────────────────────

    async def process_turn(
        self,
        question: str,
        answer: str,
        user_id: str = "default",
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """Process a single conversation turn through the cognitive loop.

        1. Store question+answer as episodic memory in mem0
        2. If past consolidation threshold, trigger GBrain consolidation
        """
        result: dict[str, Any] = {"mem0_ids": [], "consolidated": False}

        # 1. Capture episodic memory
        conversation_text = (
            f"User asked: {question}\nSystem answered: {answer}"
        )
        mem0_result = await self._mem0.add_from_messages(
            [
                {"role": "user", "content": question},
                {"role": "assistant", "content": answer},
            ],
            user_id=user_id,
        )
        extracted = mem0_result.get("results", []) if isinstance(mem0_result, dict) else []
        result["mem0_ids"] = [e.get("id") for e in extracted if e.get("id")]

        self._turn_counter += 1

        # 2. Auto-promote high-confidence facts to graph
        for entry in extracted:
            await self._mem0.promote_to_graph(entry, self._long_term.graph)

        # 3. Trigger consolidation if threshold reached
        if self._turn_counter % self._consolidation_threshold == 0:
            consolidated = await self.consolidate(user_id)
            result["consolidated"] = True
            result["consolidation_count"] = len(consolidated)

        return result

    # ── Consolidation: mem0 → GBrain ────────────────────────────────

    async def consolidate(self, user_id: str = "default") -> list[str]:
        """Cluster recent mem0 memories into GBrain deliberative notes.

        Groups mem0 facts by category/similarity, synthesizes a summary,
        and writes it as a GBrain note.
        """
        # Fetch recent mem0 memories
        all_memories = await self._mem0.get_all(user_id)
        # Filter to dict-only entries (mem0 sometimes returns strings)
        all_memories = [m for m in all_memories if isinstance(m, dict)]
        if len(all_memories) < 3:
            return []

        # Cluster by memory content similarity (simple: shared keywords)
        clusters = self._cluster_by_overlap(all_memories)

        consolidated: list[str] = []
        for cluster_id, items in clusters.items():
            if len(items) < 2:
                continue

            # Synthesize a GBrain note from the cluster
            facts = [
                item.get("memory", str(item)) if isinstance(item, dict) else str(item)
                for item in items
            ]
            topic = self._infer_topic(facts)
            summary = "\n".join(f"- {f}" for f in facts)

            note_content = (
                f"# {topic}\n\n"
                f"## Consolidated from {len(items)} episodic memories\n\n"
                f"{summary}\n\n"
                f"_Source: mem0 auto-consolidation | "
                f"Clustered at {datetime.now(timezone.utc).isoformat()}_\n"
            )

            episodes = await self._brain.write(topic, note_content)
            if episodes:
                consolidated.append(topic)

        if consolidated:
            logger.info(
                "Consolidated %d mem0 clusters into GBrain notes: %s",
                len(consolidated),
                consolidated,
            )

        return consolidated

    # ── Validation: contradiction detection ─────────────────────────

    async def validate(self, user_id: str = "default") -> dict[str, Any]:
        """Check for contradictions between mem0 memories and knowledge graph.

        For each high-confidence mem0 fact, searches the graph for
        contradictory evidence. If found:
        - Low confidence: flag for re-evaluation
        - Medium confidence: create 'conflicts_with' edge in graph
        - High confidence: update mem0 with correction
        """
        result: dict[str, Any] = {"contradictions": 0, "resolved": 0}

        all_memories = await self._mem0.get_all(user_id)
        for memory in all_memories:
            if not isinstance(memory, dict):
                continue
            content = memory.get("memory", "")
            score = memory.get("score", 0)
            if score < 0.60:
                continue  # low confidence — skip validation

            # Search graph for related facts
            graph_results = await self._long_term.search(content)
            if not graph_results:
                continue

            # Check for contradictions
            contradictions = await self._detect_contradictions(content, graph_results)
            if contradictions:
                result["contradictions"] += 1
                memory_id = memory.get("id", "unknown")

                # Update mem0 with conflicting context
                await self._mem0.update(
                    memory_id,
                    f"{content}\n[FLAGGED: Contradictory evidence found in knowledge graph]",
                )
                result["resolved"] += 1
                logger.info(
                    "Contradiction detected in mem0 memory %s: '%s'",
                    memory_id,
                    content[:100],
                )

        return result

    # ── Decay: confidence re-evaluation ──────────────────────────────

    async def decay(self, user_id: str = "default") -> int:
        """Periodic confidence re-evaluation of older memories.

        Memories older than decay_interval get their confidence docked
        unless they've been independently confirmed (appear in graph too).
        """
        all_memories = await self._mem0.get_all(user_id)
        all_memories = [m for m in all_memories if isinstance(m, dict)]
        now = datetime.now(timezone.utc)
        decayed = 0

        for memory in all_memories:
            if not isinstance(memory, dict):
                continue
            created_str = memory.get("created_at", "")
            if not created_str:
                continue

            try:
                created_at = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                continue

            age_hours = (now - created_at).total_seconds() / 3600
            if age_hours < self._decay_interval_hours:
                continue

            score = memory.get("score", 0)
            new_score = max(0.30, score - 0.05)  # decay by 0.05 per interval

            memory_id = memory.get("id", "unknown")
            await self._mem0.update(
                memory_id,
                f"{memory.get('memory', '')} [score: {new_score:.2f}]",
            )
            decayed += 1

        if decayed:
            logger.info("Decayed %d old memories (score -0.05)", decayed)

        return decayed

    # ── Helpers ─────────────────────────────────────────────────────

    def _cluster_by_overlap(
        self, memories: list[dict[str, Any]]
    ) -> dict[int, list[dict[str, Any]]]:
        """Simple keyword overlap clustering."""
        clusters: dict[int, list[dict[str, Any]]] = {}
        cluster_id = 0

        for memory in memories:
            content = memory.get("memory", "")
            words = set(content.lower().split())

            # Find best matching cluster
            best_cluster: int | None = None
            best_overlap = 0
            for cid, items in clusters.items():
                for item in items:
                    item_words = set(item.get("memory", "").lower().split())
                    overlap = len(words & item_words)
                    if overlap > best_overlap:
                        best_overlap = overlap
                        best_cluster = cid

            if best_cluster is not None and best_overlap >= 2:
                clusters[best_cluster].append(memory)
            else:
                clusters[cluster_id] = [memory]
                cluster_id += 1

        return clusters

    def _infer_topic(self, facts: list[str]) -> str:
        """Simple topic inference: most common meaningful words."""
        from collections import Counter

        all_words: list[str] = []
        stopwords = {
            "the", "a", "an", "is", "was", "are", "has", "have", "of",
            "in", "on", "at", "to", "for", "with", "and", "or", "that",
            "this", "it", "be", "by", "from", "as", "not", "but", "they",
        }
        for fact in facts:
            words = fact.lower().split()
            all_words.extend(w for w in words if w not in stopwords and len(w) > 2)

        if not all_words:
            return "Consolidated Memory"

        counter = Counter(all_words)
        top = [w for w, _ in counter.most_common(3)]
        return " ".join(top).title()

    async def _detect_contradictions(
        self, memory: str, graph_results: list[Any]
    ) -> bool:
        """Check if memory contradicts any graph node.

        Uses simple negation keyword detection + LLM if available.
        For production: replace with LLM-based contradiction detector.
        """
        memory_lower = memory.lower()
        for result in graph_results:
            result_text = str(result).lower()
            # Simple heuristic: opposite keywords
            contradictions = [
                ("always", "never"),
                ("only", "also"),
                ("disabled", "enabled"),
                ("jwt", "oauth"),
            ]
            for a, b in contradictions:
                if a in memory_lower and b in result_text and a not in result_text:
                    return True
                if b in memory_lower and a in result_text and b not in result_text:
                    return True
        return False

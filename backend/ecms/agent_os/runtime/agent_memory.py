"""Agent ↔ ECMS memory bridge for DSH-backed agents.

DSH sessions keep their own durable JSONL log, but that memory is invisible
to the rest of AegisOS. This bridge gives each agent a second memory through
the platform's Knowledge/Memory engines, aggregated across four durable
layers (each owned by its store under `ecms.memory`):

- Episodic (`memory.episodic`): prompt/response exchanges, indexed for
  semantic recall and persisted to `agent_episodes` (survives restarts).
- Procedural (`memory.procedural`): named multi-step workflows.
- Long-term (`memory.long_term`): per-agent and team-shared preferences.
- Organizational (`memory.organization`): validated team patterns.

Both directions honor the agent's `memory_scope` profile block, and nothing
secret-shaped is ever persisted (see :func:`redact_secrets`).
"""

from __future__ import annotations

import logging
import re
from typing import Any, Protocol

from ecms.memory.episodic.store import EpisodicStore
from ecms.memory.long_term.store import PreferenceStore
from ecms.memory.organization.store import PatternStore
from ecms.memory.procedural.store import ProceduralStore

logger = logging.getLogger("ecms.agent_os.agent_memory")

# Secret-shaped values are never persisted (prompt text may contain pasted keys).
_REDACT_PATTERNS = [
    re.compile(r"sk-ant-[A-Za-z0-9\-_]{8,}"),
    re.compile(r"sk-[A-Za-z0-9]{16,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9\-_.~+/]+=*"),
    re.compile(r"(?i)(api[_-]?key|auth[_-]?token|secret)\s*[:=]\s*(\"[^\"]+\"|'[^']+'|\S+)"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
]


def redact_secrets(text: str) -> str:
    """Replace secret-shaped values with [REDACTED] before persistence."""
    redacted = text
    for pattern in _REDACT_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted


def _is_episode(uco: Any) -> bool:
    """Whether a recalled object is an agent episode (vs platform knowledge)."""
    return getattr(uco, "ontology_type", "") == "agent_episode"


def _recent_first(results: list[Any]) -> list[Any]:
    """Order episodic results newest-first; keep other knowledge in rank order.

    Conversation memory is recency-biased: when several episodes match a
    query similarly (e.g. two stored codenames), the latest one is almost
    always the intended referent. Non-episodic objects keep engine order.
    """
    episodes = [uco for uco in results if _is_episode(uco)]
    rest = [uco for uco in results if uco not in episodes]

    def _created(uco: Any) -> float:
        created = getattr(uco, "created_at", None)
        timestamp = getattr(created, "timestamp", None)
        if not callable(timestamp):
            return 0.0
        try:
            value: Any = timestamp()
            return float(value)
        except Exception:
            return 0.0

    episodes.sort(key=_created, reverse=True)
    return episodes + rest


class MemoryEngineLike(Protocol):
    """Structural slice of DefaultMemoryEngine used for recall."""

    async def retrieve(self, query: str, *, limit: int = 10) -> list[Any]: ...


class KnowledgeRepoLike(Protocol):
    """Structural slice of the knowledge repository used for episodic writes."""

    async def add(self, uco: Any) -> None: ...


class AgentMemoryBridge:
    """Connects DSH agent sessions to the ECMS memory layers."""

    def __init__(
        self,
        memory: MemoryEngineLike,
        repository: KnowledgeRepoLike,
        uco_factory: Any | None = None,
    ) -> None:
        self._memory = memory
        self.episodes = EpisodicStore(repository, uco_factory)
        self.procedures = ProceduralStore()
        self.preferences = PreferenceStore()
        self.patterns = PatternStore()

    async def recall(
        self,
        query: str,
        scope: dict[str, Any] | None,
        *,
        agent_id: str = "",
        limit: int = 3,
        max_chars: int = 2000,
    ) -> str:
        """Return relevant past knowledge as prompt context ("" when none).

        Aggregates episodic exchanges, matching procedures, agent + shared
        preferences, and matching org patterns.
        """
        scope = scope or {}
        # Agent-owned memory: gate on the read flag only. Business categories
        # (project_context, decisions, …) govern curated knowledge, not the
        # agent's own conversation history.
        if not scope.get("read", True):
            return ""
        sections: list[str] = []
        try:
            # Over-fetch: hash-embedding rank order is noisy, so pull extra
            # candidates and let recency (episodes) and rank (knowledge) trim.
            results = await self._memory.retrieve(query, limit=limit + 7)
        except Exception as e:
            logger.warning("Memory recall failed: %s", e)
            results = []
        ordered = _recent_first(results)
        trimmed = [uco for uco in ordered if _is_episode(uco)][
            :limit
        ] + [uco for uco in ordered if not _is_episode(uco)][:limit]
        blocks = []
        for uco in trimmed:
            text = f"{uco.display_name}: {uco.description}"
            if text.strip():
                blocks.append(text)
        if blocks:
            sections.append("Past episodes:\n" + "\n".join(blocks))
        try:
            procedures = await self.recall_procedures(query, limit=2)
        except Exception as e:
            logger.warning("Procedure recall failed: %s", e)
            procedures = []
        if procedures:
            sections.append(
                "Known procedures:\n"
                + "\n".join(f"- {p['name']}: {'; '.join(p['steps'])}" for p in procedures)
            )
        try:
            prefs = await self.recall_preferences(agent_id) if agent_id else {}
        except Exception as e:
            logger.warning("Preference recall failed: %s", e)
            prefs = {}
        if prefs:
            sections.append(
                "Preferences:\n" + "\n".join(f"- {k}: {v}" for k, v in prefs.items())
            )
        try:
            patterns = await self.search_patterns(query, limit=2)
        except Exception as e:
            logger.warning("Pattern recall failed: %s", e)
            patterns = []
        if patterns:
            sections.append(
                "Team patterns:\n"
                + "\n".join(f"- [{p['pattern_type']}] {p['description']}" for p in patterns)
            )
        return "\n".join(sections)[:max_chars]

    async def record_exchange(
        self,
        agent_id: str,
        prompt: str,
        response: str,
        scope: dict[str, Any] | None,
    ) -> None:
        """Store one prompt/response pair (scope-gated, secrets redacted)."""
        scope = scope or {}
        if not scope.get("write", False):
            return
        try:
            await self.episodes.save(
                agent_id, redact_secrets(prompt), redact_secrets(response)
            )
            logger.debug("Recorded memory episode for agent %s", agent_id)
        except Exception as e:
            logger.warning("Memory write failed for agent %s: %s", agent_id, e)

    async def backfill_from_db(self) -> int:
        """Reload persisted episodes into the in-memory index (startup)."""
        return await self.episodes.backfill()

    async def learn_procedure(
        self,
        name: str,
        description: str,
        steps: list[str],
        learned_by: str,
    ) -> dict[str, Any]:
        """Store a named multi-step workflow; returns its record."""
        return await self.procedures.learn(
            name, redact_secrets(description), steps, learned_by
        )

    async def recall_procedures(self, query: str, limit: int = 3) -> list[dict[str, Any]]:
        """Return procedures whose name/description shares a keyword with the query."""
        return await self.procedures.search(query, limit=limit)

    async def remember(
        self, key: str, value: str, agent_id: str, *, shared: bool = False
    ) -> None:
        """Store a long-term preference (per-agent, or team-shared)."""
        await self.preferences.remember(key, redact_secrets(value), agent_id, shared=shared)

    async def recall_preferences(self, agent_id: str) -> dict[str, str]:
        """Return shared prefs overlaid with the agent's own (agent wins)."""
        return await self.preferences.recall(agent_id)

    async def publish_pattern(
        self, pattern_type: str, description: str, published_by: str
    ) -> dict[str, Any]:
        """Publish a validated best practice / known bug / convention / optimization."""
        return await self.patterns.publish(
            pattern_type, redact_secrets(description), published_by
        )

    async def search_patterns(self, query: str, limit: int = 3) -> list[dict[str, Any]]:
        """Return patterns whose description shares a keyword with the query."""
        return await self.patterns.search(query, limit=limit)

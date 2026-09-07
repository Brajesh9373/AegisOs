"""Agent ↔ ECMS memory bridge for DSH-backed agents.

DSH sessions keep their own durable JSONL log, but that memory is invisible
to the rest of AegisOS. This bridge gives each agent a second memory through
the platform's Knowledge/Memory engines:

- Read: before a prompt goes to DSH, `recall` pulls the most relevant
  cognitive objects and prepends them as context.
- Write: after the agent responds, `record_exchange` stores the prompt/response
  pair as an episodic UCO so later prompts (and other agents) can recall it.

Both directions honor the agent's `memory_scope` profile block:
`read`/`write` flags plus the allowed `categories` list (empty = unrestricted).
"""

from __future__ import annotations

import logging
import re
import time
from typing import Any, Protocol

logger = logging.getLogger("ecms.agent_os.agent_memory")

# Secret-shaped values are never persisted (prompt text may contain pasted keys).
_REDACT_PATTERNS = [
    re.compile(r"sk-ant-[A-Za-z0-9\-_]{8,}"),
    re.compile(r"sk-[A-Za-z0-9]{16,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"(?i)(api[_-]?key|auth[_-]?token|bearer|secret)\s*[:=]\s*(\"[^\"]+\"|'[^']+'|\S+)"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
]


def redact_secrets(text: str) -> str:
    """Replace secret-shaped values with [REDACTED] before persistence."""
    redacted = text
    for pattern in _REDACT_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted


class MemoryEngineLike(Protocol):
    """Structural slice of DefaultMemoryEngine used for recall."""

    async def retrieve(self, query: str, *, limit: int = 10) -> list[Any]: ...


class KnowledgeRepoLike(Protocol):
    """Structural slice of the knowledge repository used for episodic writes."""

    async def add(self, uco: Any) -> None: ...


class AgentMemoryBridge:
    """Connects DSH agent sessions to the ECMS memory/knowledge engines."""

    #: UCO category tag for stored agent exchanges.
    EPISODIC_CATEGORY = "agent_episode"

    def __init__(
        self,
        memory: MemoryEngineLike,
        repository: KnowledgeRepoLike,
        uco_factory: Any | None = None,
    ) -> None:
        self._memory = memory
        self._repository = repository
        # UCO class (UniversalCognitiveObject); imported lazily to keep this
        # module importable without the full shared-models chain in unit tests.
        self._uco_factory = uco_factory

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

        Aggregates four layers: episodic exchanges, matching procedures,
        agent + shared preferences, and matching org patterns.
        """
        scope = scope or {}
        # Agent-owned memory: gate on the read flag only. Business categories
        # (project_context, decisions, …) govern curated knowledge, not the
        # agent's own conversation history.
        if not scope.get("read", True):
            return ""
        sections: list[str] = []
        try:
            results = await self._memory.retrieve(query, limit=limit)
        except Exception as e:
            logger.warning("Memory recall failed: %s", e)
            results = []
        blocks = []
        for uco in results:
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

    # ── Procedural memory ─────────────────────────────────────────────

    async def learn_procedure(
        self,
        name: str,
        description: str,
        steps: list[str],
        learned_by: str,
    ) -> dict[str, Any]:
        """Store a named multi-step workflow; returns its record."""
        import uuid as _uuid

        from ecms.persistence.database.rest_session import db_session
        from ecms.persistence.models.agent_memory_layers import AgentProcedure

        await self._ensure_layer_tables()
        record = AgentProcedure(
            id=f"proc-{_uuid.uuid4().hex[:12]}",
            name=name.strip(),
            description=redact_secrets(description.strip()),
            steps=[s.strip() for s in steps if s.strip()],
            learned_by=learned_by,
        )
        async with db_session() as session:
            session.add(record)
        logger.info("Learned procedure %r from %s", name, learned_by)
        return record.to_dict()

    async def recall_procedures(self, query: str, limit: int = 3) -> list[dict[str, Any]]:
        """Return procedures whose name/description shares a keyword with the query."""
        from sqlalchemy import select

        from ecms.persistence.database.rest_session import db_session
        from ecms.persistence.models.agent_memory_layers import AgentProcedure

        tokens = {t for t in re.findall(r"[a-z0-9]+", query.lower()) if len(t) > 3}
        if not tokens:
            return []
        try:
            async with db_session() as session:
                rows = (await session.execute(select(AgentProcedure))).scalars().all()
        except Exception as e:
            logger.warning("Procedure recall failed: %s", e)
            return []
        scored = []
        for row in rows:
            haystack = f"{row.name} {row.description}".lower()
            overlap = sum(1 for t in tokens if t in haystack)
            if overlap:
                scored.append((overlap, row))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [row.to_dict() for _, row in scored[:limit]]

    # ── Long-term preferences ─────────────────────────────────────────

    @staticmethod
    def _preference_scopes(agent_id: str) -> list[str]:
        scopes = ["team:shared"]
        if agent_id:
            scopes.append(f"agent:{agent_id}")
        return scopes

    async def remember(self, key: str, value: str, agent_id: str, *, shared: bool = False) -> None:
        """Store a long-term preference (per-agent, or team-shared)."""
        from ecms.persistence.database.rest_session import db_session
        from ecms.persistence.models.agent_memory_layers import AgentPreference

        await self._ensure_layer_tables()
        scope = "team:shared" if shared else f"agent:{agent_id}"
        async with db_session() as session:
            from sqlalchemy import select as _select

            existing = (
                await session.execute(
                    _select(AgentPreference).where(
                        AgentPreference.scope == scope, AgentPreference.key == key
                    )
                )
            ).scalar_one_or_none()
            if existing is None:
                session.add(
                    AgentPreference(
                        scope=scope, key=key, value=redact_secrets(value),
                        updated_by=agent_id,
                    )
                )
            else:
                existing.value = redact_secrets(value)
                existing.updated_by = agent_id

    async def recall_preferences(self, agent_id: str) -> dict[str, str]:
        """Return shared prefs overlaid with the agent's own (agent wins)."""
        from sqlalchemy import select

        from ecms.persistence.database.rest_session import db_session
        from ecms.persistence.models.agent_memory_layers import AgentPreference

        try:
            async with db_session() as session:
                rows = (
                    await session.execute(
                        select(AgentPreference).where(
                            AgentPreference.scope.in_(self._preference_scopes(agent_id))
                        )
                    )
                ).scalars().all()
        except Exception as e:
            logger.warning("Preference recall failed: %s", e)
            return {}
        prefs: dict[str, str] = {}
        for row in sorted(rows, key=lambda r: r.scope):
            prefs[row.key] = row.value
        return prefs

    # ── Organizational patterns ───────────────────────────────────────

    async def publish_pattern(
        self, pattern_type: str, description: str, published_by: str
    ) -> dict[str, Any]:
        """Publish a validated best practice / known bug / convention / optimization."""
        import uuid as _uuid

        from ecms.persistence.database.rest_session import db_session
        from ecms.persistence.models.agent_memory_layers import OrgPattern

        allowed = {"best_practice", "known_bug", "optimization", "convention"}
        if pattern_type not in allowed:
            raise ValueError(f"pattern_type must be one of {sorted(allowed)}")
        await self._ensure_layer_tables()
        record = OrgPattern(
            id=f"pat-{_uuid.uuid4().hex[:12]}",
            pattern_type=pattern_type,
            description=redact_secrets(description.strip()),
            published_by=published_by,
        )
        async with db_session() as session:
            session.add(record)
        logger.info("Published %s pattern from %s", pattern_type, published_by)
        return record.to_dict()

    async def search_patterns(self, query: str, limit: int = 3) -> list[dict[str, Any]]:
        """Return patterns whose description shares a keyword with the query."""
        from sqlalchemy import select

        from ecms.persistence.database.rest_session import db_session
        from ecms.persistence.models.agent_memory_layers import OrgPattern

        tokens = {t for t in re.findall(r"[a-z0-9]+", query.lower()) if len(t) > 3}
        if not tokens:
            return []
        try:
            async with db_session() as session:
                rows = (await session.execute(select(OrgPattern))).scalars().all()
        except Exception as e:
            logger.warning("Pattern search failed: %s", e)
            return []
        scored = []
        for row in rows:
            haystack = f"{row.pattern_type} {row.description}".lower()
            overlap = sum(1 for t in tokens if t in haystack)
            if overlap:
                scored.append((overlap, row))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [row.to_dict() for _, row in scored[:limit]]

    async def _ensure_layer_tables(self) -> None:
        """Create layer tables when missing (checkfirst; migrations are canonical)."""
        import os

        from sqlalchemy.ext.asyncio import create_async_engine

        from ecms.persistence.models.agent_memory_layers import (
            AgentPreference,
            AgentProcedure,
            OrgPattern,
        )

        url = os.environ.get("ECMS_DATABASE_URL", "sqlite+aiosqlite:///./ecms.db")
        engine = create_async_engine(url)
        try:
            async with engine.begin() as connection:
                for table in (
                    AgentProcedure.__table__,
                    AgentPreference.__table__,
                    OrgPattern.__table__,
                ):
                    await connection.run_sync(table.create, checkfirst=True)
        finally:
            await engine.dispose()

    async def record_exchange(
        self,
        agent_id: str,
        prompt: str,
        response: str,
        scope: dict[str, Any] | None,
    ) -> None:
        """Store one prompt/response pair as an episodic UCO.

        Writes to the in-memory index (fast recall) and to the
        `agent_episodes` table (survives restarts; backfilled on boot).
        """
        scope = scope or {}
        if not scope.get("write", False):
            return
        if self._uco_factory is None:
            try:
                from ecms.shared.models import UniversalCognitiveObject
            except ImportError as e:
                logger.warning("Memory write skipped (no UCO model): %s", e)
                return
            self._uco_factory = UniversalCognitiveObject
        summary = response.strip().split("\n")[0][:280] if response.strip() else "(no response)"
        prompt = redact_secrets(prompt)
        response = redact_secrets(response)
        try:
            uco = self._uco_factory(
                canonical_name=f"agent-episode-{agent_id}-{int(time.time() * 1000)}",
                display_name=f"Agent episode ({agent_id})",
                ontology_type="agent_episode",
                description=f"Q: {prompt.strip()[:500]}\nA: {response.strip()[:500]}",
                summary=summary,
                created_by=agent_id,
                custom_attributes={
                    "agent_id": agent_id,
                    "category": self.EPISODIC_CATEGORY,
                    "prompt": prompt.strip()[:2000],
                    "response": response.strip()[:2000],
                },
            )
            await self._repository.add(uco)
            await self._persist_episode(agent_id, uco)
            logger.debug("Recorded memory episode for agent %s", agent_id)
        except Exception as e:
            logger.warning("Memory write failed for agent %s: %s", agent_id, e)

    async def backfill_from_db(self) -> int:
        """Reload persisted episodes into the in-memory index (startup).

        Creates the table when missing (dev/test convenience; production uses
        alembic migrations) and re-indexes every stored UCO. Returns the
        number of episodes restored.
        """
        try:
            from sqlalchemy import select

            from ecms.persistence.database.rest_session import db_session
            from ecms.persistence.models.agent_episode import AgentEpisode
        except ImportError as e:
            logger.warning("Memory backfill skipped (no persistence layer): %s", e)
            return 0
        try:
            await self._ensure_episode_table()
            async with db_session() as session:
                rows = (
                    await session.execute(
                        select(AgentEpisode).order_by(AgentEpisode.created_at)
                    )
                ).scalars().all()
            restored = 0
            for row in rows:
                uco = self._row_to_uco(row)
                if uco is None:
                    continue
                try:
                    await self._repository.add(uco)
                    restored += 1
                except Exception as e:
                    logger.warning("Skipping episode %s on backfill: %s", row.uco_id, e)
            if restored:
                logger.info("Backfilled %d agent episodes into memory", restored)
            return restored
        except Exception as e:
            logger.warning("Memory backfill failed: %s", e)
            return 0

    async def _persist_episode(self, agent_id: str, uco: Any) -> None:
        """Write one episode row; failures stay local (memory stays best-effort)."""
        try:
            from ecms.persistence.database.rest_session import db_session
            from ecms.persistence.models.agent_episode import AgentEpisode
        except ImportError as e:
            logger.warning("Episode persistence skipped: %s", e)
            return
        try:
            dump = uco.model_dump(mode="json") if hasattr(uco, "model_dump") else {}
            async with db_session() as session:
                session.add(
                    AgentEpisode(
                        uco_id=uco.uco_id,
                        agent_id=agent_id,
                        display_name=uco.display_name,
                        description=uco.description,
                        summary=uco.summary or "",
                        ontology_type=uco.ontology_type,
                        uco_json=dump,
                    )
                )
        except Exception as e:
            logger.warning("Episode persistence failed for agent %s: %s", agent_id, e)

    async def _ensure_episode_table(self) -> None:
        """Create agent_episodes when missing (checkfirst; migration is canonical)."""
        import os

        from sqlalchemy.ext.asyncio import create_async_engine

        from ecms.persistence.models.agent_episode import AgentEpisode

        url = os.environ.get("ECMS_DATABASE_URL", "sqlite+aiosqlite:///./ecms.db")
        engine = create_async_engine(url)
        try:
            async with engine.begin() as connection:
                await connection.run_sync(
                    AgentEpisode.__table__.create, checkfirst=True
                )
        finally:
            await engine.dispose()

    def _row_to_uco(self, row: Any) -> Any | None:
        """Rebuild a UCO from its stored snapshot."""
        if self._uco_factory is None:
            try:
                from ecms.shared.models import UniversalCognitiveObject
            except ImportError:
                return None
            self._uco_factory = UniversalCognitiveObject
        data = row.uco_json or {}
        try:
            return self._uco_factory.model_validate(data)
        except Exception:
            # Fallback: rebuild the searchable core from columns.
            try:
                return self._uco_factory(
                    canonical_name=f"agent-episode-{row.agent_id}-{row.uco_id}",
                    display_name=row.display_name,
                    ontology_type=row.ontology_type,
                    description=row.description,
                    summary=row.summary,
                    created_by=row.agent_id,
                    custom_attributes={"agent_id": row.agent_id},
                )
            except Exception:
                return None

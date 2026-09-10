"""Discovery service — transactional, idempotent state machine for BA discovery.

Router is thin; this service owns all DB + LLM orchestration and the
idempotency/rollback guarantees. Each operation is atomic: LLM calls happen
outside the final state-commit, and retries replay from cached state instead
of 400 INVALID-TRANSITION.

This service now uses the Agent OS BA profile plugin for execution.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException
from sqlalchemy import text

from ecms.agent.ba.plugin import get_ba_profile_catalog
from ecms.agent_os.profiles.contracts import TerminalResult
from ecms.persistence.database.rest_session import db_session

logger = logging.getLogger("ecms.discovery.service")


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _row_to_dict(row) -> dict:
    if not row:
        return {}
    return {k.lower(): v for k, v in row._mapping.items()}


async def _load_session_for_update(session_id: str, db) -> dict:
    # FOR UPDATE is postgres-only; sqlite serializes writers anyway.
    lock = "" if db.bind.dialect.name == "sqlite" else " FOR UPDATE"
    row = (
        await db.execute(
            text(f"SELECT * FROM discovery_sessions WHERE id=:id{lock}"), {"id": session_id}
        )
    ).first()
    if not row:
        raise HTTPException(
            status_code=404, detail={"error": "NOT-FOUND", "message": "Discovery session not found"}
        )
    d = _row_to_dict(row)
    if isinstance(d.get("messages"), str):
        d["messages"] = json.loads(d["messages"])
    if isinstance(d.get("requirements"), str):
        d["requirements"] = json.loads(d["requirements"])
    return d


class DiscoveryService:
    """Application service for discovery sessions using Agent OS BA profile."""

    def __init__(self) -> None:
        """Initialize with BA profile catalog."""
        self._catalog = get_ba_profile_catalog()
        self._profile = self._catalog.resolve("business-analyst")

    async def analyze(self, session_id: str, identity: Any = None) -> dict:
        """Atomic analyze using BA profile: succeed → CLARIFYING, fail → stay INGESTED, retry → idempotent."""
        # Load session data first - keep it in scope for the whole method
        async with db_session() as db:
            lock = "" if db.bind.dialect.name == "sqlite" else " FOR UPDATE"
            row = (
                await db.execute(
                    text(f"SELECT * FROM discovery_sessions WHERE id=:id{lock}"),
                    {"id": session_id},
                )
            ).first()
            if not row:
                raise HTTPException(
                    status_code=404,
                    detail={"error": "NOT-FOUND", "message": "Discovery session not found"},
                )
            sess = _row_to_dict(row)
            if isinstance(sess.get("messages"), str):
                sess["messages"] = json.loads(sess["messages"])
            stage = sess.get("stage") or ""

            if stage == "CLARIFYING":
                msgs = sess.get("messages") or []
                if len(msgs) >= 2:
                    last = msgs[-1]
                    prev = msgs[-2] if len(msgs) >= 2 else {}
                    return {
                        "session_id": session_id,
                        "stage": "CLARIFYING",
                        "recap": prev.get("content", ""),
                        "questions": last.get("content", ""),
                        "category": last.get("category"),
                        "category_label": last.get("category_label"),
                    }

            if stage not in ("INGESTED", "UNDERSTANDING"):
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "INVALID-TRANSITION",
                        "message": f"Cannot analyze from {stage}",
                    },
                )

            source = (sess.get("source_text") or "").strip()
            if not source:
                raise HTTPException(
                    status_code=400,
                    detail={"error": "NO-INPUT", "message": "No source text ingested yet"},
                )

            if stage == "UNDERSTANDING":
                await db.execute(
                    text(
                        "UPDATE discovery_sessions SET stage='INGESTED', updated_at=:t WHERE id=:id"
                    ),
                    {"t": _now(), "id": session_id},
                )

            # Keep messages in scope for later use
            conversation = sess.get("messages", [])

        # Get knowledge context using the existing retrieval
        from ecms.agent.ba.agent import retrieve_knowledge

        knowledge_context = await retrieve_knowledge(source)

        # Execute understand stage through BA profile
        understand_spec = self._profile.stage_spec("understand")
        understand_request = {
            "source_text": source,
            "knowledge_context": knowledge_context,
        }
        self._profile.validate_request(understand_spec, understand_request)
        understand_prompt = self._profile.render_prompt(understand_spec, understand_request)

        # Execute through LLM (reuse existing BA agent for now)
        from ecms.agent.ba.agent import understand

        recap = await understand(source, knowledge_context=knowledge_context)

        # Execute clarify stage through BA profile
        clarify_spec = self._profile.stage_spec("clarify")
        clarify_request = {
            "source_text": source,
            "conversation": conversation,
            "knowledge_context": knowledge_context,
        }
        self._profile.validate_request(clarify_spec, clarify_request)
        clarify_prompt = self._profile.render_prompt(clarify_spec, clarify_request)

        # Execute clarify through existing BA agent
        from ecms.agent.ba.agent import clarify

        clarification = await clarify(source, knowledge_context=knowledge_context)

        # Validate results using profile
        understand_result = TerminalResult(
            envelope_version="aegis.agent-step.v1",
            outcome="terminal",
            stage_id="understand",
            result=recap,
        )
        self._profile.validate_terminal_result(understand_spec, understand_result)

        clarify_result = TerminalResult(
            envelope_version="aegis.agent-step.v1",
            outcome="terminal",
            stage_id="clarify",
            result=clarification,
        )
        self._profile.validate_terminal_result(clarify_spec, clarify_result)

        # Persist results
        async with db_session() as db:
            lock = "" if db.bind.dialect.name == "sqlite" else " FOR UPDATE"
            row = (
                await db.execute(
                    text(f"SELECT messages, stage FROM discovery_sessions WHERE id=:id{lock}"),
                    {"id": session_id},
                )
            ).first()
            if row and row[1] == "CLARIFYING":
                msgs = row[0] if isinstance(row[0], list) else json.loads(row[0] or "[]")
                if len(msgs) >= 2:
                    last = msgs[-1]
                    prev = msgs[-2]
                    return {
                        "session_id": session_id,
                        "stage": "CLARIFYING",
                        "recap": prev.get("content", ""),
                        "questions": last.get("content", ""),
                        "category": last.get("category"),
                        "category_label": last.get("category_label"),
                    }

            raw_row = (
                await db.execute(
                    text("SELECT messages FROM discovery_sessions WHERE id=:id"), {"id": session_id}
                )
            ).first()
            raw = raw_row[0] if raw_row and raw_row[0] else []
            if isinstance(raw, list):
                msgs = raw
            elif isinstance(raw, str):
                msgs = json.loads(raw)
            else:
                msgs = []

            now = _now()
            msgs.append({"role": "assistant", "content": recap, "timestamp": now})
            msgs.append(
                {
                    "role": "assistant",
                    "content": clarification["content"],
                    "timestamp": now,
                    "category": clarification["category"],
                    "category_label": clarification["category_label"],
                }
            )
            await db.execute(
                text(
                    "UPDATE discovery_sessions SET messages=:m, stage='CLARIFYING', updated_at=:t WHERE id=:id"
                ),
                {"m": json.dumps(msgs), "t": now, "id": session_id},
            )

        return {
            "session_id": session_id,
            "stage": "CLARIFYING",
            "recap": recap,
            "questions": clarification["content"],
            "category": clarification["category"],
            "category_label": clarification["category_label"],
        }

    async def get_session(self, session_id: str) -> dict:
        async with db_session() as db:
            row = (
                await db.execute(
                    text("SELECT * FROM discovery_sessions WHERE id=:id"), {"id": session_id}
                )
            ).first()
            if not row:
                raise HTTPException(
                    status_code=404,
                    detail={"error": "NOT-FOUND", "message": "Discovery session not found"},
                )
            d = _row_to_dict(row)
            if isinstance(d.get("messages"), str):
                d["messages"] = json.loads(d["messages"])
            if isinstance(d.get("requirements"), str):
                d["requirements"] = json.loads(d["requirements"])
            return d


# Module-level singleton for discovery service
_discovery_service: DiscoveryService | None = None


def get_discovery_service() -> DiscoveryService:
    """Get the discovery service singleton."""
    global _discovery_service
    if _discovery_service is None:
        _discovery_service = DiscoveryService()
    return _discovery_service

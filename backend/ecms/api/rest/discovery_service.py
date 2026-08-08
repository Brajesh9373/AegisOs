"""Discovery service — transactional, idempotent state machine for BA discovery.

Router is thin; this service owns all DB + LLM orchestration and the
idempotency/rollback guarantees. Each operation is atomic: LLM calls happen
outside the final state-commit, and retries replay from cached state instead
of 400 INVALID-TRANSITION.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import text

from ecms.persistence.database.rest_session import db_session
from ecms.shared.exceptions import ConflictError

logger = logging.getLogger("ecms.discovery.service")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row_to_dict(row) -> dict:
    if not row:
        return {}
    return {k.lower(): v for k, v in row._mapping.items()}


async def _load_session_for_update(session_id: str, db) -> dict:
    row = (await db.execute(text("SELECT * FROM discovery_sessions WHERE id=:id FOR UPDATE"), {"id": session_id})).first()
    if not row:
        raise HTTPException(status_code=404, detail={"error": "NOT-FOUND", "message": "Discovery session not found"})
    d = _row_to_dict(row)
    if isinstance(d.get("messages"), str):
        d["messages"] = json.loads(d["messages"])
    if isinstance(d.get("requirements"), str):
        d["requirements"] = json.loads(d["requirements"])
    return d


class DiscoveryService:
    """Application service for discovery sessions."""

    async def analyze(self, session_id: str) -> dict:
        """Atomic analyze: succeed → CLARIFYING, fail → stay INGESTED, retry → idempotent."""
        from ecms.agent.ba.agent import clarify, retrieve_knowledge, understand

        async with db_session() as db:
            row = (await db.execute(text("SELECT * FROM discovery_sessions WHERE id=:id FOR UPDATE"), {"id": session_id})).first()
            if not row:
                raise HTTPException(status_code=404, detail={"error": "NOT-FOUND", "message": "Discovery session not found"})
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
                raise HTTPException(status_code=400, detail={"error": "INVALID-TRANSITION", "message": f"Cannot analyze from {stage}"})

            source = (sess.get("source_text") or "").strip()
            if not source:
                raise HTTPException(status_code=400, detail={"error": "NO-INPUT", "message": "No source text ingested yet"})

            if stage == "UNDERSTANDING":
                await db.execute(text("UPDATE discovery_sessions SET stage='INGESTED', updated_at=:t WHERE id=:id"), {"t": _now(), "id": session_id})

        knowledge_context = await retrieve_knowledge(source)

        recap = await understand(source, knowledge_context=knowledge_context)
        clarification = await clarify(source, knowledge_context=knowledge_context)

        async with db_session() as db:
            row = (await db.execute(text("SELECT messages, stage FROM discovery_sessions WHERE id=:id FOR UPDATE"), {"id": session_id})).first()
            if row and row[0] == "CLARIFYING":
                msgs = row[1] if isinstance(row[1], list) else json.loads(row[1] or "[]")
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

            raw_row = (await db.execute(text("SELECT messages FROM discovery_sessions WHERE id=:id"), {"id": session_id})).first()
            raw = raw_row[0] if raw_row and raw_row[0] else []
            if isinstance(raw, list):
                msgs = raw
            elif isinstance(raw, str):
                msgs = json.loads(raw)
            else:
                msgs = []

            now = _now()
            msgs.append({"role": "assistant", "content": recap, "timestamp": now})
            msgs.append({"role": "assistant", "content": clarification["content"], "timestamp": now, "category": clarification["category"], "category_label": clarification["category_label"]})
            await db.execute(text("UPDATE discovery_sessions SET messages=:m, stage='CLARIFYING', updated_at=:t WHERE id=:id"), {"m": json.dumps(msgs), "t": now, "id": session_id})

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
            row = (await db.execute(text("SELECT * FROM discovery_sessions WHERE id=:id"), {"id": session_id})).first()
            if not row:
                raise HTTPException(status_code=404, detail={"error": "NOT-FOUND", "message": "Discovery session not found"})
            d = _row_to_dict(row)
            if isinstance(d.get("messages"), str):
                d["messages"] = json.loads(d["messages"])
            if isinstance(d.get("requirements"), str):
                d["requirements"] = json.loads(d["requirements"])
            return d

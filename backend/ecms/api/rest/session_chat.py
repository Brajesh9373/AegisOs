"""Session chat endpoint — agentic ReAct loop with direct memory tools.

The agent owns memory. No pre-injection, no command-code subprocess.
User prompt → AgentLoop (LLM + tools) → response → capture to memory.

Sessions and messages are now persisted in PostgreSQL for full history replay.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from legacy_ecms.config import get_settings
from legacy_ecms.memory.cognitive_orchestrator import CognitiveOrchestrator

__all__ = ["router", "sync_all_memory"]

router = APIRouter(prefix="/sessions", tags=["sessions"])

_STORE: "FileMemoryStore | None" = None


def _get_store() -> "FileMemoryStore":
    global _STORE
    if _STORE is None:
        from legacy_ecms.memory.stores.file_store import FileMemoryStore
        _STORE = FileMemoryStore(Path("/app/memory"))
    return _STORE


async def sync_all_memory() -> dict:
    """Sync FalkorDB + GBrain into atom store. Called at startup."""
    import asyncio as _asyncio
    from legacy_ecms.memory.bridge import UnifiedMemoryBridge
    store = _get_store()
    bridge = UnifiedMemoryBridge(Path("/app/memory"))
    try:
        synced = await _asyncio.to_thread(bridge.sync_all, store)
        return {"synced": synced, "total": store.atom_count()}
    except Exception as e:
        return {"synced": 0, "total": store.atom_count(), "error": str(e)}


# ── Models ────────────────────────────────────────────────────────────


class CreateSessionRequest(BaseModel):
    workspace_id: str | None = None
    title: str | None = None
    project_id: str | None = None


class ChatRequest(BaseModel):
    prompt: str
    workspace_id: str | None = None
    model: str | None = None
    model_api_key: str | None = None
    model_base_url: str | None = None
    agent_id: str | None = None


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    trace: dict[str, object] | None = None
    memory_updated: bool = False
    provenance: dict[str, object] | None = None


async def _get_session_repo():
    from ecms.persistence.database.rest_session import db_session as pg_session
    from ecms.persistence.repositories.session import SessionRepository
    return pg_session, SessionRepository


class _SessionRepo:
    @staticmethod
    async def persist_message(session_id: str, role: str, content: str | None = None) -> None:
        try:
            pg, Repo = await _get_session_repo()
            async with pg() as s:
                await Repo(s).add_message(session_id, role=role, content=content)
        except Exception:
            pass

    @staticmethod
    async def ensure(session_id: str, workspace_id: str | None, title: str | None = None, project_id: str | None = None) -> None:
        try:
            pg, Repo = await _get_session_repo()
            async with pg() as s:
                r = Repo(s)
                if await r.get(session_id) is None:
                    await r.create(
                        session_id=session_id,
                        workspace_id=workspace_id or "default",
                        title=title,
                        project_id=project_id,
                    )
        except Exception:
            pass


# ── Endpoints ─────────────────────────────────────────────────────────


@router.post("")
async def create_session(body: CreateSessionRequest = CreateSessionRequest()) -> dict:
    session_id = str(uuid.uuid4())
    workspace_id = body.workspace_id or "default"

    # Persist in PostgreSQL
    await _SessionRepo.ensure(session_id, workspace_id, body.title, body.project_id)

    return {
        "session_id": session_id,
        "status": "created",
        "workspace_id": workspace_id,
    }


@router.post("/{session_id}/chat")
async def session_chat(session_id: str, body: ChatRequest):
    """Agentic chat — streams task plan + progress via SSE."""

    workspace_id = body.workspace_id or "default"

    # Ensure session exists in DB
    await _SessionRepo.ensure(session_id, workspace_id)

    # Persist user message
    await _SessionRepo.persist_message(session_id, "user", body.prompt)

    from ecms.agent.loop import AgentLoop

    # Load agent profile synchronously before creating AgentLoop
    agent_profile = None
    if body.agent_id:
        try:
            from ecms.persistence.database.rest_session import db_session as _pg_db
            from sqlalchemy import text as _text
            async with _pg_db() as _s:
                row = (await _s.execute(
                    _text("SELECT system_prompt_addon, tool_policy FROM agents WHERE id = :aid"),
                    {"aid": body.agent_id},
                )).first()
                if row:
                    d = {k.lower(): v for k, v in row._mapping.items() if v is not None}
                    agent_profile = d
        except Exception:
            pass

    queue: asyncio.Queue[dict | None] = asyncio.Queue()

    # Background task: run the agent, push events to queue
    async def _run_agent():
        # Check if this agent should show task progress
        show_progress = True
        if body.agent_id:
            try:
                from ecms.persistence.database.rest_session import db_session as pg_db
                from sqlalchemy import text as _text
                async with pg_db() as s:
                    row = (await s.execute(
                        _text("SELECT show_task_progress FROM agents WHERE id = :aid"),
                        {"aid": body.agent_id},
                    )).first()
                    if row:
                        show_progress = bool(row[0])
            except Exception:
                pass

        def _on_progress(data: dict):
            if not show_progress:
                return
            try:
                queue.put_nowait({
                    "type": "task_progress",
                    "id": "1",
                    "title": "Agent working",
                    "iteration": data.get("iteration", 0),
                    "tool_name": data.get("tool_name", ""),
                })
            except asyncio.QueueFull:
                pass

        loop = AgentLoop(
            session_id,
            model=body.model or None,
            api_key=body.model_api_key or None,
            base_url=body.model_base_url or None,
            progress_callback=_on_progress,
            agent_profile=agent_profile,
        )
        answer, trace = await loop.run(body.prompt)

        # Detect [_FINALIZE_READY_] marker in agent response
        show_finalize = False
        if answer and "[_FINALIZE_READY_]" in answer:
            show_finalize = True
            answer = answer.replace("[_FINALIZE_READY_]", "").strip()
            # Clean up double spaces left by marker removal
            import re as _re
            answer = _re.sub(r'  +', ' ', answer)

        await queue.put({
            "type": "answer",
            "content": answer or "I was unable to complete my reasoning.",
            "show_finalize": show_finalize,
        })
        await queue.put(None)  # Sentinel: done

    async def _stream():
        # Phase: understanding
        yield f"data: {json.dumps({'type': 'status', 'phase': 'understanding'})}\n\n"

        # Start agent in background
        task = asyncio.create_task(_run_agent())

        answer = None
        while True:
            event = await queue.get()
            if event is None:  # Sentinel
                break
            if event.get("type") == "answer":
                answer = event["content"]
            yield f"data: {json.dumps(event)}\n\n"

        await task  # Ensure agent finished cleanly

        # ── Persist to PostgreSQL ──
        if answer:
            await _SessionRepo.persist_message(session_id, "assistant", answer)

        # ── Memory capture (fire-and-forget) ───────────────────────
        settings = get_settings()
        memory_updated = False

        # Episodic: record conversation event
        async def _record_episode():
            try:
                from ecms.memory.episodic import get_event_store
                store = get_event_store()
                store.record(session_id, body.prompt, answer)
            except Exception:
                pass
        asyncio.create_task(_record_episode())

        if getattr(settings, "mem0_enabled", False):
            async def _capture():
                nonlocal memory_updated
                try:
                    orch = CognitiveOrchestrator(settings, workspace_id=workspace_id)
                    await orch.process_turn(body.prompt, answer, session_id, session_id)
                    memory_updated = True
                except Exception:
                    pass
            asyncio.create_task(_capture())

        # ── GBrain capture + structured atom store ──────────────────
        try:
            from legacy_ecms.memory.brain import GBrain
            from legacy_ecms.memory.stores.file_store import FileMemoryStore
            from legacy_ecms.memory.extraction import ConversationExtractor

            store = FileMemoryStore(Path("/app/memory"))
            brain = GBrain(Path("/app/memory"))
            await brain.write(
                f"Chat: {body.prompt[:60]}",
                f"**Q:** {body.prompt}\n\n**A:** {answer[:2000]}",
            )
            extractor = ConversationExtractor(store, min_confidence=0.70, max_atoms_per_conversation=8)
            await extractor.extract_and_persist(
                question=body.prompt,
                answer=answer,
                session_id=session_id,
            )
        except Exception:
            pass

    return StreamingResponse(
        _stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ── Session listing ──────────────────────────────────────────────────


@router.get("")
async def list_sessions(workspace_id: str | None = Query(None)) -> dict:
    """Return sessions for a workspace from PostgreSQL, falling back to episode store."""

    # Try PostgreSQL first
    if workspace_id:
        try:
            from ecms.persistence.database.rest_session import db_session as pg_session
            from ecms.persistence.repositories.session import SessionRepository
            async with pg_session() as s:
                repo = SessionRepository(s)
                db_sessions = await repo.list_by_workspace(workspace_id, limit=50)
                if db_sessions:
                    return {
                        "sessions": [
                            {
                                "session_id": ses.id,
                                "title": ses.title or f"Session {ses.id[:8]}",
                                "last_active": ses.updated_at.isoformat() if ses.updated_at else "",
                                "message_count": len(ses.messages) if ses.messages else 0,
                            }
                            for ses in db_sessions
                        ]
                    }
        except Exception:
            pass

    # Fallback: episode store (legacy)
    try:
        from ecms.memory.episodic import get_event_store
        store = get_event_store()
        episodes = store.recent(limit=50)
        sessions: dict[str, dict] = {}
        for ep in episodes:
            sid = ep.get("session_id", "unknown")
            if sid not in sessions:
                sessions[sid] = {
                    "session_id": sid,
                    "last_question": ep.get("question", "")[:100],
                    "last_active": ep.get("timestamp", ""),
                    "message_count": 1,
                }
            else:
                sessions[sid]["message_count"] += 1
        return {"sessions": sorted(sessions.values(), key=lambda s: s["last_active"], reverse=True)}
    except Exception:
        return {"sessions": []}


# ── Message history ──────────────────────────────────────────────────


@router.get("/{session_id}/messages")
async def get_messages(session_id: str) -> dict:
    """Return full chat message history for a session from PostgreSQL.

    Falls back to file-based conversation history for legacy sessions.
    """
    try:
        from ecms.persistence.database.rest_session import db_session as pg_session
        from ecms.persistence.repositories.session import SessionRepository
        async with pg_session() as s:
            repo = SessionRepository(s)
            msgs = await repo.get_messages(session_id)
            if msgs:
                return {"messages": msgs}
    except Exception:
        pass

    # Fallback: file-based conversation history
    try:
        conv = Conversation(session_id)
        file_msgs = conv.as_list()
        return {
            "messages": [
                {
                    "id": f"file-{i}",
                    "role": m.get("role", "unknown"),
                    "content": m.get("content", ""),
                    "tool_calls": m.get("tool_calls"),
                    "tool_call_id": m.get("tool_call_id"),
                    "name": m.get("name"),
                    "created_at": "",
                }
                for i, m in enumerate(file_msgs)
            ]
        }
    except Exception:
        pass

    return {"messages": []}


# ── Delete a session ─────────────────────────────────────────────────


@router.delete("/{session_id}")
async def delete_session(session_id: str) -> dict:
    """Delete a single chat session and its messages."""
    try:
        from ecms.persistence.database.rest_session import db_session as pg_session
        from ecms.persistence.repositories.session import SessionRepository
        async with pg_session() as s:
            repo = SessionRepository(s)
            deleted = await repo.delete(session_id)
            if deleted:
                await s.commit()
                return {"status": "deleted", "session_id": session_id}
    except Exception:
        pass
    return {"status": "not_found", "session_id": session_id}

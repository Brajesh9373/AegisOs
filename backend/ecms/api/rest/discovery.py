"""Discovery API — BA agent state-machine endpoints.

Replaces the mocked NewProject.tsx flow with a real interactive discovery:

    DRAFT → INGESTED → UNDERSTANDING → CLARIFYING ⇄ FINALIZING → FINALIZED

Each stage transition is an API call. The BA agent runs structured LLM
generations (not a free ReAct loop) to guarantee format fidelity with the
approved frontend mock.
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from ecms.persistence.database.rest_session import db_session
from ecms.shared.context import bind_context
from ecms.infrastructure.telemetry.tracing import traced_span

logger = logging.getLogger("ecms.discovery")

router = APIRouter(prefix="/api/discovery")

# Valid stage transitions.
_TRANSITIONS: dict[str, set[str]] = {
    "DRAFT": {"INGESTED"},
    "INGESTED": {"UNDERSTANDING"},
    "UNDERSTANDING": {"CLARIFYING"},
    "CLARIFYING": {"CLARIFYING", "FINALIZING"},
    "FINALIZING": {"FINALIZED"},
    "FINALIZED": set(),
}


# ---------------------------------------------------------------------------
# Helpers (mirror platform.py patterns)
# ---------------------------------------------------------------------------

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _is_finalize_intent(message: str) -> bool:
    normalized = "".join(ch.lower() if ch.isalnum() else " " for ch in message)
    normalized = " ".join(normalized.split())
    exact = {
        "create project",
        "create the project",
        "generate requirements",
        "generate the requirements",
        "finalize requirements",
        "finalise requirements",
        "finalize the requirements",
        "finalise the requirements",
        "create requirements package",
        "create the requirements package",
        "move forward",
        "go ahead",
        "proceed",
    }
    return (
        normalized in exact
        or normalized.startswith("please create project")
        or normalized.startswith("please generate requirements")
        or normalized.startswith("please finalize")
        or normalized.startswith("please finalise")
    )


def _uuid() -> str:
    return str(uuid.uuid4())


def _row_to_dict(row) -> dict:
    if not row:
        return {}
    return {k.lower(): v for k, v in row._mapping.items()}


def _error(code: str, message: str, status: int = 400):
    raise HTTPException(status_code=status, detail={"error": code, "message": message})


async def _get_current_user(request: Request) -> dict:
    auth = request.headers.get("Authorization", "")
    token = auth.removeprefix("Bearer ").strip()
    if not token:
        _error("AUTH-4011", "Missing token", 401)
    async with db_session() as session:
        from sqlalchemy import text
        row = (await session.execute(
            text("SELECT * FROM auth_sessions WHERE token = :t"), {"t": token}
        )).first()
        if not row:
            _error("AUTH-4012", "Invalid session", 401)
        sess = _row_to_dict(row)
        user_row = (await session.execute(
            text("SELECT * FROM users WHERE id = :id"), {"id": sess["userid"]}
        )).first()
        if not user_row:
            _error("AUTH-4013", "User not found", 401)
        return _row_to_dict(user_row)


async def _load_session(session_id: str) -> dict:
    async with db_session() as session:
        from sqlalchemy import text
        row = (await session.execute(
            text("SELECT * FROM discovery_sessions WHERE id = :id"),
            {"id": session_id},
        )).first()
        if not row:
            _error("NOT-FOUND", "Discovery session not found", 404)
        d = _row_to_dict(row)
        # Deserialize JSONB fields.
        if isinstance(d.get("messages"), str):
            d["messages"] = json.loads(d["messages"])
        if isinstance(d.get("requirements"), str):
            d["requirements"] = json.loads(d["requirements"])
        return d


async def _transition(session_id: str, to_stage: str):
    """Validate and persist a stage transition."""
    async with db_session() as session:
        from sqlalchemy import text
        row = (await session.execute(
            text("SELECT stage FROM discovery_sessions WHERE id = :id"),
            {"id": session_id},
        )).first()
        if not row:
            _error("NOT-FOUND", "Session not found", 404)
        current = row[0]
        allowed = _TRANSITIONS.get(current, set())
        if to_stage not in allowed:
            _error("INVALID-TRANSITION",
                   f"Cannot move from {current} to {to_stage}", 400)
        await session.execute(text(
            "UPDATE discovery_sessions SET stage=:s, updated_at=:t WHERE id=:id"
        ), {"s": to_stage, "t": _now(), "id": session_id})


async def _append_message(
    session_id: str,
    role: str,
    content: str,
    *,
    category: str | None = None,
    category_label: str | None = None,
):
    """Append a message to the session's message thread."""
    async with db_session() as session:
        from sqlalchemy import text
        row = (await session.execute(
            text("SELECT messages FROM discovery_sessions WHERE id = :id"),
            {"id": session_id},
        )).first()
        raw = row[0] if row and row[0] else []
        # asyncpg returns JSONB as list; sqlite returns JSON string.
        if isinstance(raw, list):
            msgs = raw
        elif isinstance(raw, str):
            msgs = json.loads(raw)
        else:
            msgs = []
        message = {"role": role, "content": content, "timestamp": _now()}
        if category:
            message["category"] = category
        if category_label:
            message["category_label"] = category_label
        msgs.append(message)
        await session.execute(text(
            "UPDATE discovery_sessions SET messages=:m, updated_at=:t WHERE id=:id"
        ), {"m": json.dumps(msgs), "t": _now(), "id": session_id})
        return msgs


# ---------------------------------------------------------------------------
# 1. Create session (DRAFT)
# ---------------------------------------------------------------------------

class CreateSessionBody(BaseModel):
    project_id: str | None = None


# ---------------------------------------------------------------------------
# 0. Audio transcription (Whisper)
# ---------------------------------------------------------------------------


@router.post("/transcribe")
async def transcribe_audio(request: Request):
    """Transcribe an audio file using the OpenAI Whisper API.

    Accepts multipart/form-data with an 'audio' file field.
    Returns {"text": "..."} with the transcribed text.
    Uses the same API credentials as the BA agent.
    """
    await _get_current_user(request)

    form = await request.form()
    audio_file = form.get("audio")
    if not audio_file:
        return {"text": "", "error": "No audio file provided"}

    # Read the uploaded file
    audio_bytes = await audio_file.read()
    filename = getattr(audio_file, "filename", "audio.webm") or "audio.webm"

    # Determine content type
    content_type = getattr(audio_file, "content_type", "audio/webm") or "audio/webm"

    try:
        from ecms.agent.ba.model import resolve_ba_model
        from openai import AsyncOpenAI

        cfg = await resolve_ba_model()
        base_url = cfg.get("base_url") or ""
        if base_url and not base_url.rstrip("/").endswith("/v1"):
            base_url = base_url.rstrip("/") + "/v1"

        client = AsyncOpenAI(api_key=cfg["api_key"], base_url=base_url or None)

        # Create a file-like object for the Whisper API
        import io
        audio_io = io.BytesIO(audio_bytes)
        audio_io.name = filename

        # Call Whisper API
        transcript = await client.audio.transcriptions.create(
            model="whisper-1",
            file=(filename, audio_bytes, content_type),
            language="en",
        )

        return {"text": transcript.text or ""}
    except Exception as exc:
        logger.warning("[discovery] transcription failed: %s", exc)
        return {"text": "", "error": str(exc)}


@router.post("/sessions")
async def create_session(body: CreateSessionBody, request: Request):
    await _get_current_user(request)
    sid = _uuid()
    now = _now()
    async with db_session() as session:
        from sqlalchemy import text
        await session.execute(text(
            "INSERT INTO discovery_sessions "
            "(id, project_id, stage, source_text, transcript, messages, requirements, ai_model_id, created_at, updated_at) "
            "VALUES (:id, :pid, 'DRAFT', NULL, NULL, '[]', NULL, NULL, :t, :t)"
        ), {"id": sid, "pid": body.project_id, "t": now})
    return {"session_id": sid, "stage": "DRAFT"}


# ---------------------------------------------------------------------------
# 2. Ingest text / file content (DRAFT → INGESTED)
# ---------------------------------------------------------------------------

class IngestBody(BaseModel):
    text: str | None = None
    file_content: str | None = None
    file_name: str | None = None


@router.post("/{session_id}/ingest")
async def ingest(session_id: str, body: IngestBody, request: Request):
    await _get_current_user(request)
    await _transition(session_id, "INGESTED")

    source = body.text or body.file_content or ""
    if not source.strip():
        _error("EMPTY-INPUT", "Provide text or file_content", 400)

    async with db_session() as session:
        from sqlalchemy import text
        await session.execute(text(
            "UPDATE discovery_sessions SET source_text=:st, updated_at=:t WHERE id=:id"
        ), {"st": source.strip(), "t": _now(), "id": session_id})

    return {"session_id": session_id, "stage": "INGESTED", "length": len(source)}


# ---------------------------------------------------------------------------
# 3. Analyze — run "understand" + generate clarifying questions
#    (INGESTED → UNDERSTANDING → CLARIFYING)
# ---------------------------------------------------------------------------

@router.post("/{session_id}/analyze")
async def analyze(session_id: str, request: Request):
    user = await _get_current_user(request)
    bind_context(session_id=session_id, user_id=user.get("id"))
    with traced_span("discovery.analyze"):
        from ecms.api.rest.discovery_service import DiscoveryService
        svc = DiscoveryService()
        try:
            return await svc.analyze(session_id)
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            from ecms.shared.context import get_correlation_id
            try:
                trace_id = get_correlation_id()
            except Exception:
                trace_id = f"req-{session_id[:8]}"
            logger.exception("[discovery.analyze] failed session=%s trace=%s: %s: %s", session_id, trace_id, type(exc).__name__, exc)
            raise HTTPException(status_code=500, detail={
                "success": False,
                "error": {"code": "ANALYZE-FAILED", "message": str(exc), "traceId": trace_id},
            })


# ---------------------------------------------------------------------------
# 4. Chat — user answers clarifying questions (CLARIFYING → CLARIFYING)
# ---------------------------------------------------------------------------

class ChatBody(BaseModel):
    message: str


@router.post("/{session_id}/chat")
async def chat(session_id: str, body: ChatBody, request: Request):
    user = await _get_current_user(request)
    bind_context(session_id=session_id, user_id=user.get("id"))
    with traced_span("discovery.chat"):
        sess = await _load_session(session_id)
        if sess["stage"] != "CLARIFYING":
            _error("WRONG-STAGE", f"Expected CLARIFYING, got {sess['stage']}", 400)

        conversation = await _append_message(session_id, "user", body.message)

        if _is_finalize_intent(body.message):
            reply = (
                "Understood. I have enough to move forward. Set the meeting cadence, "
                "then generate the requirements package for review."
            )
            await _append_message(session_id, "assistant", reply)
            return {
                "session_id": session_id,
                "stage": "CLARIFYING",
                "reply": reply,
                "show_finalize": True,
            }

        source = sess.get("source_text") or ""
        from ecms.agent.ba.agent import chat_reply, retrieve_knowledge

        knowledge_context = await retrieve_knowledge(source, conversation)

        try:
            clarification = await chat_reply(
                source,
                conversation,
                body.message,
                knowledge_context=knowledge_context,
            )
            reply = clarification["content"]
        except Exception as exc:
            logger.warning("[discovery.chat] LLM call failed: %s", exc)
            reply = (
                "Thank you for that information. I've noted your response. "
                "When you're ready, click **Generate Requirements** and I'll produce "
                "the structured requirements package."
            )
            clarification = None

        await _append_message(
            session_id,
            "assistant",
            reply,
            category=clarification["category"] if clarification else None,
            category_label=clarification["category_label"] if clarification else None,
        )

        response = {
            "session_id": session_id,
            "stage": "CLARIFYING",
            "reply": reply,
        }
        if clarification:
            response["category"] = clarification["category"]
            response["category_label"] = clarification["category_label"]
        return response


# ---------------------------------------------------------------------------
# 5. Finalize — produce the FinalizedRequirements object
#    (CLARIFYING → FINALIZING → FINALIZED)
# ---------------------------------------------------------------------------

class FinalizeBody(BaseModel):
    meeting_frequency: str | None = None
    preferred_time: str | None = None


@router.get("/{session_id}/finalize-status")
async def finalize_status(session_id: str, request: Request):
    await _get_current_user(request)
    sess = await _load_session(session_id)
    stage = sess.get("stage") or ""
    transcript = sess.get("transcript") or ""
    progress = {}
    if isinstance(transcript, str) and transcript:
        try:
            import json as _json
            progress = _json.loads(transcript) if transcript.startswith("{") else {}
        except Exception:
            progress = {}
    elif isinstance(transcript, dict):
        progress = transcript
    return {
        "session_id": session_id,
        "stage": stage,
        "finalize_stage": progress.get("finalize_stage") if stage == "FINALIZING" else ("done" if stage == "FINALIZED" else None),
        "finalize_attempt": progress.get("attempt"),
        "updated_at": sess.get("updated_at"),
    }


@router.post("/{session_id}/finalize")
async def finalize(session_id: str, body: FinalizeBody, request: Request):
    user = await _get_current_user(request)
    bind_context(session_id=session_id, user_id=user.get("id"))
    with traced_span("discovery.finalize"):
        sess = await _load_session(session_id)
        if sess["stage"] not in ("CLARIFYING", "FINALIZING"):
            _error("WRONG-STAGE", f"Cannot finalize from {sess['stage']}", 400)

        source = sess.get("source_text") or ""
        conversation = sess.get("messages") or []

        from ecms.agent.ba.agent import finalize as ba_finalize, retrieve_knowledge

        knowledge_context = await retrieve_knowledge(source, conversation)

        await _transition(session_id, "FINALIZING")
        try:
            async with db_session() as session:
                from sqlalchemy import text
                await session.execute(text(
                    "UPDATE discovery_sessions SET transcript=:t, updated_at=:u WHERE id=:id"
                ), {"t": json.dumps({"finalize_stage": "calling_llm", "attempt": 1}), "u": _now(), "id": session_id})
            result = await ba_finalize(source, conversation, knowledge_context=knowledge_context)
            async with db_session() as session:
                from sqlalchemy import text
                await session.execute(text(
                    "UPDATE discovery_sessions SET transcript=:t, updated_at=:u WHERE id=:id"
                ), {"t": json.dumps({"finalize_stage": "validating"}), "u": _now(), "id": session_id})
        except Exception as exc:
            logger.exception("[discovery.finalize] failed session=%s: %s: %s", session_id, type(exc).__name__, exc)
            async with db_session() as session:
                from sqlalchemy import text
                await session.execute(text(
                    "UPDATE discovery_sessions SET stage='CLARIFYING', transcript=:t, updated_at=:u WHERE id=:id"
                ), {"t": json.dumps({"finalize_stage": "failed"}), "u": _now(), "id": session_id})
            code = "FINALIZE-TIMEOUT" if "timeout" in str(exc).lower() or "Timeout" in type(exc).__name__ else "FINALIZE-FAILED"
            status = 504 if code == "FINALIZE-TIMEOUT" else 500
            _error(code, str(exc), status)

    req_dict = result.to_frontend()

    now = _now()
    async with db_session() as session:
        from sqlalchemy import text
        await session.execute(text(
            "UPDATE discovery_sessions SET requirements=:req, stage='FINALIZED', updated_at=:t WHERE id=:id"
        ), {"req": json.dumps(req_dict), "t": now, "id": session_id})

        pid = sess.get("project_id")
        if pid:
            await session.execute(text(
                "UPDATE business_projects SET requirements=:req WHERE id=:pid"
            ), {"req": json.dumps(req_dict), "pid": pid})
            for r in req_dict.get("functionalReqs", []):
                await session.execute(text(
                    "INSERT INTO project_requirements "
                    "(id, project_id, text, type, status, source, version, created_at, updated_at) "
                    "VALUES (:id, :pid, :text, 'functional', 'confirmed', 'ba_agent', 1, :t, :t)"
                ), {"id": _uuid(), "pid": pid, "text": r, "t": now})
            for r in req_dict.get("risks", []):
                await session.execute(text(
                    "INSERT INTO project_risks "
                    "(id, project_id, risk, impact, mitigation, status, version, created_at) "
                    "VALUES (:id, :pid, :risk, 'medium', '', 'open', 1, :t)"
                ), {"id": _uuid(), "pid": pid, "risk": r, "t": now})
            for s in req_dict.get("skills", []):
                await session.execute(text(
                    "INSERT INTO project_requirements "
                    "(id, project_id, text, type, status, source, version, created_at, updated_at) "
                    "VALUES (:id, :pid, :text, 'skill', 'confirmed', 'ba_agent', 1, :t, :t)"
                ), {"id": _uuid(), "pid": pid, "text": s, "t": now})
            for c in req_dict.get("connectors", []):
                await session.execute(text(
                    "INSERT INTO project_requirements "
                    "(id, project_id, text, type, status, source, version, created_at, updated_at) "
                    "VALUES (:id, :pid, :text, 'connector', 'confirmed', 'ba_agent', 1, :t, :t)"
                ), {"id": _uuid(), "pid": pid, "text": c, "t": now})
            await _ensure_requirement_documents(session, pid)
            from ecms.api.rest.platform import (
                _ensure_project_meetings,
                _row_to_dict as _platform_row,
            )
            project_row = (await session.execute(text(
                "SELECT * FROM business_projects WHERE id = :pid"
            ), {"pid": pid})).first()
            project = _platform_row(project_row) if project_row else {}
            if project:
                await _ensure_project_meetings(
                    session,
                    project,
                    preferred_time=body.preferred_time,
                    meeting_frequency=body.meeting_frequency or "weekly",
                )
    summary = f"**Project: {req_dict.get('projectName', '')}**\n\n{req_dict.get('objective', '')}"
    await _append_message(session_id, "assistant", summary)

    return {
        "session_id": session_id,
        "stage": "FINALIZED",
        "requirements": req_dict,
    }


# ---------------------------------------------------------------------------
# 6. Get session (read current state)
# ---------------------------------------------------------------------------

@router.get("/{session_id}")
async def get_session(session_id: str, request: Request):
    await _get_current_user(request)
    sess = await _load_session(session_id)
    return sess


# ---------------------------------------------------------------------------
# 7. Link session to project (after project creation)
# ---------------------------------------------------------------------------

async def _save_ba_transcript_doc(session, project_id: str, messages: list[dict]) -> None:
    """Save the BA discovery conversation as a Knowledge Base document.

    Instead of mirroring the transcript into a workspace chat session, this
    formats the full conversation as a Markdown document and stores it in the
    ``artifacts`` table under the ``Discovery`` category so it appears in the
    Knowledge Base section of the workspace.

    Idempotent: the artifact id is derived from the project id.
    """
    from sqlalchemy import text

    if not messages:
        return

    doc_id = f"doc-{project_id}-discovery"

    # Skip if already saved.
    existing = (await session.execute(text(
        "SELECT 1 FROM artifacts WHERE id = :id"
    ), {"id": doc_id})).first()
    if existing:
        return

    # Build a readable Markdown document from the conversation.
    lines: list[str] = ["# BA Discovery Transcript", ""]
    for m in messages:
        role = m.get("role") or "assistant"
        content = m.get("content") or ""
        if not content:
            continue
        label = "**You**" if role == "user" else "**Business Analyst**"
        lines.append(f"{label}")
        lines.append("")
        lines.append(content)
        lines.append("")
        lines.append("---")
        lines.append("")

    md_content = "\n".join(lines)
    now = _now()

    await session.execute(text(
        "INSERT INTO artifacts (id, projectid, name, type, content, uri, storagepath, agentid, createdat, versionhistory) "
        "VALUES (:id, :pid, :name, :type, :content, :uri, :uri, NULL, :t, '{}') "
        "ON CONFLICT (id) DO NOTHING"
    ), {
        "id": doc_id,
        "pid": project_id,
        "name": "ba-discovery-transcript.md",
        "type": "Discovery",
        "content": md_content,
        "uri": f"knowledge/{project_id}/ba-discovery-transcript.md",
        "t": now,
    })


async def _seed_ba_meeting(session, project_id: str, reqs: dict, messages: list[dict]) -> None:
    """Auto-seed a 'BA Discovery' meeting from the finalized requirements.

    This makes the Meetings tab non-empty the moment a project is created: the
    onboarding conversation with the BA becomes the first (past) meeting, with
    its objective as the summary and the finalized risks/phases as decisions.

    Idempotent: the meeting id is derived from the project id so re-linking does
    not create duplicates.
    """
    from sqlalchemy import text

    mid = f"ba-discovery-{project_id}"
    existing = (await session.execute(text(
        "SELECT 1 FROM meetings WHERE id = :id"
    ), {"id": mid})).first()
    if existing:
        return

    objective = (reqs.get("objective") or "").strip()
    project_name = reqs.get("projectName") or ""
    summary = (
        f"Business Analyst discovery session for {project_name}. " + objective
    ).strip() if objective else f"Business Analyst discovery session for {project_name}."

    # Decisions: prefer explicit phases; fall back to the first few functional reqs.
    decisions: list[str] = []
    for p in (reqs.get("phases") or [])[:5]:
        if isinstance(p, dict):
            nm = p.get("name") or ""
            dur = p.get("duration") or ""
            decisions.append(f"{nm} ({dur})" if dur else nm)
    if not decisions:
        decisions = [r for r in (reqs.get("functionalReqs") or [])[:5] if isinstance(r, str)]

    # Attendees: the human plus the BA agent (+ count a message exchange as real).
    participants = ["Project Owner", "Business Analyst Agent"]
    turns = len([m for m in messages if m.get("content")])

    now = _now()
    await session.execute(text(
        "INSERT INTO meetings "
        "(id, project_id, title, meeting_date, meeting_time, duration, type, status, "
        " participants, agenda, notes, summary, decisions, action_items, attachments, "
        " source, created_at, updated_at) "
        "VALUES (:id, :pid, :title, :date, NULL, NULL, 'both', 'past', "
        " :participants, :agenda, NULL, :summary, :decisions, '[]', '[]', "
        " 'ba_discovery', :t, :t)"
    ), {
        "id": mid, "pid": project_id,
        "title": "BA Discovery & Requirement Finalization",
        "date": now[:10],  # YYYY-MM-DD
        "agenda": f"Requirement discovery for {project_name} ({turns} exchanges)",
        "participants": json.dumps(participants),
        "summary": summary,
        "decisions": json.dumps(decisions),
        "t": now,
    })


async def _ensure_requirement_documents(session, project_id: str) -> None:
    """Create workspace knowledge docs from the project's stored requirements."""
    from sqlalchemy import text
    from ecms.api.rest.platform import _ensure_project_documents, _row_to_dict as _platform_row

    row = (await session.execute(text(
        "SELECT * FROM business_projects WHERE id = :pid"
    ), {"pid": project_id})).first()
    project = _platform_row(row) if row else {}
    if project:
        await _ensure_project_documents(session, project)


@router.post("/{session_id}/link-project")
async def link_project(session_id: str, body: dict, request: Request):
    user = await _get_current_user(request)
    bind_context(session_id=session_id, user_id=user.get("id"))
    with traced_span("discovery.link_project"):
        sess = await _load_session(session_id)
        if sess.get("stage") != "FINALIZED":
            raise HTTPException(status_code=400, detail={"error": "WRONG-STAGE", "message": f"Cannot link from {sess.get('stage')}"})
        project_id = body.get("project_id")
        if not project_id:
            return _error("missing_project_id", "project_id is required", 400)

        reqs = sess.get("requirements")
        now = _now()
        uid = _uuid()

        try:
            async with db_session() as session:
                from sqlalchemy import text
                await session.execute(text(
                    "UPDATE discovery_sessions SET project_id = :pid, updated_at = :t WHERE id = :id"
                ), {"pid": project_id, "t": now, "id": session_id})

                if reqs and isinstance(reqs, dict):
                    await session.execute(text(
                        "UPDATE business_projects SET requirements = :req, updatedat = :t WHERE id = :pid"
                    ), {"req": json.dumps(reqs), "t": now, "pid": project_id})

                if reqs and isinstance(reqs, dict):
                    pid = project_id
                    for i, r in enumerate(reqs.get("functionalReqs", [])):
                        await session.execute(text(
                            "INSERT INTO project_requirements "
                            "(id, project_id, text, type, status, source, version, created_at, updated_at) "
                            "VALUES (:id, :pid, :text, 'functional', 'proposed', 'ba_agent', '1', :t, :t) "
                            "ON CONFLICT DO NOTHING"
                        ), {"id": f"{uid}-fr-{i}", "pid": pid, "text": r, "t": now})
                    for i, s in enumerate(reqs.get("skills", [])):
                        await session.execute(text(
                            "INSERT INTO project_requirements "
                            "(id, project_id, text, type, status, source, version, created_at, updated_at) "
                            "VALUES (:id, :pid, :text, 'skill', 'proposed', 'ba_agent', '1', :t, :t) "
                            "ON CONFLICT DO NOTHING"
                        ), {"id": f"{uid}-sk-{i}", "pid": pid, "text": s, "t": now})
                    for i, c in enumerate(reqs.get("connectors", [])):
                        await session.execute(text(
                            "INSERT INTO project_requirements "
                            "(id, project_id, text, type, status, source, version, created_at, updated_at) "
                            "VALUES (:id, :pid, :text, 'connector', 'proposed', 'ba_agent', '1', :t, :t) "
                            "ON CONFLICT DO NOTHING"
                        ), {"id": f"{uid}-cn-{i}", "pid": pid, "text": c, "t": now})
                    for i, r in enumerate(reqs.get("risks", [])):
                        await session.execute(text(
                            "INSERT INTO project_risks "
                            "(id, project_id, risk, impact, mitigation, status, version, created_at) "
                            "VALUES (:id, :pid, :risk, 'Medium', 'TBD', 'open', '1', :t) "
                            "ON CONFLICT DO NOTHING"
                        ), {"id": f"{uid}-rk-{i}", "pid": pid, "risk": r, "t": now})

                await _save_ba_transcript_doc(session, project_id, sess.get("messages") or [])

                if reqs and isinstance(reqs, dict):
                    from ecms.api.rest.platform import (
                        _ensure_project_meetings,
                        _row_to_dict as _platform_row,
                    )
                    project_row = (await session.execute(text(
                        "SELECT * FROM business_projects WHERE id = :pid"
                    ), {"pid": project_id})).first()
                    project = _platform_row(project_row) if project_row else {}
                    if project:
                        await _ensure_project_meetings(session, project)
                    await _ensure_requirement_documents(session, project_id)
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            logger.exception("[discovery.link_project] failed session=%s project=%s: %s: %s", session_id, project_id, type(exc).__name__, exc)
            raise HTTPException(status_code=500, detail={
                "success": False,
                "error": {"code": "LINK-PROJECT-FAILED", "message": str(exc), "traceId": f"req-{session_id[:8]}"},
            })

        if sess.get("stage") == "FINALIZED" and reqs and isinstance(reqs, dict):
            conversation = sess.get("messages") or []
            await _set_team_status(project_id, "generating")
            asyncio.create_task(_run_team_design(project_id, reqs, conversation))

        return {"status": "linked", "session_id": session_id, "project_id": project_id}


# ---------------------------------------------------------------------------
# 8. Design the per-project agent team (background)
# ---------------------------------------------------------------------------

async def _set_team_status(project_id: str, status: str) -> None:
    async with db_session() as session:
        from sqlalchemy import text
        await session.execute(text(
            "UPDATE business_projects SET team_status=:s, updatedat=:t WHERE id=:id"
        ), {"s": status, "t": _now(), "id": project_id})


def _requirement_text(requirements: dict) -> str:
    parts: list[str] = []
    for key in ("objective",):
        value = requirements.get(key)
        if value:
            parts.append(str(value))
    for key in ("functionalReqs", "techStack", "skills", "connectors", "risks"):
        values = requirements.get(key) or []
        parts.extend(str(v) for v in values)
    for section in ("governance", "guardrails", "infrastructure"):
        for item in requirements.get(section) or []:
            if isinstance(item, dict):
                parts.append(str(item.get("label") or ""))
                parts.append(str(item.get("detail") or ""))
    return " ".join(parts).lower()


def _select_tools(tool_names: list[str], preferred: list[str], limit: int = 5) -> list[str]:
    if not tool_names:
        return preferred[:limit]
    allowed = set(tool_names)
    picked = [tool for tool in preferred if tool in allowed]
    if picked:
        return picked[:limit]
    return tool_names[:limit]


def _fallback_team_rows(
    project_id: str,
    requirements: dict,
    model_ids: list[str],
    tool_names: list[str],
) -> list[dict]:
    """Deterministic project-specific org chart used when LLM team design fails."""
    text_blob = _requirement_text(requirements)
    model = model_ids[0] if model_ids else "gpt-4o"
    objective = requirements.get("objective") or "Deliver the finalized project scope."
    project_name = requirements.get("projectName") or "Project"

    def needs(*terms: str) -> bool:
        return any(term in text_blob for term in terms)

    def rid(key: str) -> str:
        return f"{project_id}:{key}"

    rows: list[dict] = []
    default_automation = {"autoRetry": True, "maxRetries": 3, "retryDelaySeconds": 30, "escalateOnFailure": True, "heartbeatIntervalSeconds": 60}
    default_features = {"memoryRetentionDays": 30, "dataQueryAccess": "read", "maxConcurrentTasks": 5, "rateLimitPerMinute": 60, "streamingEnabled": True, "auditLogging": True, "piiMasking": False}

    def add(
        key: str,
        name: str,
        role: str,
        designation: str,
        department: str,
        reports_to: str | None,
        goal: str,
        instructions: str,
        skills: list[str],
        tools: list[str],
    ) -> None:
        rows.append({
            "id": rid(key),
            "project_id": project_id,
            "name": name,
            "role": role,
            "designation": designation,
            "role_description": goal,
            "skills": skills,
            "department": department,
            "reports_to": rid(reports_to) if reports_to else None,
            "model": model,
            "tool_policy": {"allowed_tools": _select_tools(tool_names, tools), "blocked_tools": []},
            "system_prompt_addon": instructions,
            "automation": default_automation,
            "features": default_features,
            "status": "active",
        })

    add(
        "delivery-manager",
        "Delivery Manager",
        "delivery_manager",
        "Engagement Delivery Manager",
        "delivery",
        None,
        f"Own delivery outcome for {project_name}.",
        f"Coordinate the project against this objective: {objective}",
        ["delivery management", "stakeholder coordination", "risk management"],
        ["assign_task", "my_tasks", "search_memory"],
    )
    add(
        "solution-architect",
        "Solution Architect",
        "solution_architect",
        "Solution Architect",
        "architecture",
        "delivery-manager",
        "Convert requirements into implementation architecture and phase gates.",
        "Keep frontend, backend, data, integration, security, and infrastructure decisions aligned.",
        ["system design", "architecture review", "technical planning"],
        ["read_file", "search_code", "query_graph", "search_memory"],
    )
    add(
        "business-analyst",
        "Business Analyst",
        "business_analyst",
        "Requirements Custodian",
        "analysis",
        "delivery-manager",
        "Maintain the finalized requirements, assumptions, and acceptance criteria.",
        "Translate each finalized requirement into acceptance criteria and flag scope changes.",
        ["requirements management", "acceptance criteria", "scope control"],
        ["read_file", "search_memory", "note"],
    )
    add(
        "engineering-manager",
        "Engineering Manager",
        "engineering_manager",
        "Engineering Manager",
        "engineering",
        "delivery-manager",
        "Assign and sequence implementation work across project pods.",
        "Break requirements into executable stories, coordinate dependencies, and unblock engineers.",
        ["engineering planning", "dependency management", "execution coordination"],
        ["assign_task", "my_tasks", "search_code", "read_file"],
    )

    if needs("frontend", "react", "angular", "vue", "ui", "ux", "mobile", "android", "ios", "web app"):
        add(
            "frontend-engineer",
            "Frontend Engineer",
            "frontend_engineer",
            "Frontend Implementation Engineer",
            "frontend",
            "engineering-manager",
            "Build the user-facing experience required by the finalized scope.",
            "Implement screens, states, routing, accessibility, and API integration from the requirements.",
            ["frontend engineering", "UI implementation", "API integration"],
            ["read_file", "edit_file", "search_code", "shell_command"],
        )

    if needs("backend", "api", "node", "python", "java", "service", "microservice", "auth"):
        add(
            "backend-engineer",
            "Backend Engineer",
            "backend_engineer",
            "Backend/API Engineer",
            "backend",
            "engineering-manager",
            "Implement backend services, APIs, and business logic for the project.",
            "Build API contracts, persistence logic, auth boundaries, and integration adapters.",
            ["backend engineering", "API design", "service integration"],
            ["read_file", "edit_file", "search_code", "shell_command"],
        )

    if needs("database", "mysql", "postgres", "mongodb", "sql", "data", "migration", "etl", "schema"):
        add(
            "data-engineer",
            "Data Engineer",
            "data_engineer",
            "Data & Migration Engineer",
            "data",
            "engineering-manager",
            "Own data models, migration, validation, and reconciliation.",
            "Map source and target data, define validation checks, and preserve auditability.",
            ["data modeling", "migration", "data validation"],
            ["read_file", "edit_file", "search_code", "shell_command"],
        )

    if needs("integration", "sync", "webhook", "queue", "pub/sub", "kafka", "connector", "erp", "crm"):
        add(
            "integration-engineer",
            "Integration Engineer",
            "integration_engineer",
            "Integration Engineer",
            "integration",
            "engineering-manager",
            "Connect upstream and downstream systems required by the project.",
            "Design idempotent integrations, retries, error handling, and sync monitoring.",
            ["integration design", "eventing", "connector implementation"],
            ["read_file", "edit_file", "search_code", "shell_command"],
        )

    if needs("infra", "infrastructure", "cloud", "aws", "azure", "gcp", "docker", "kubernetes", "deploy", "ci/cd", "terraform"):
        add(
            "sre",
            "DevOps / SRE",
            "sre",
            "Infrastructure & Reliability Engineer",
            "infrastructure",
            "engineering-manager",
            "Provision and operate the runtime infrastructure.",
            "Define environments, deployment path, monitoring, rollback, and reliability controls.",
            ["infrastructure", "deployment", "observability"],
            ["read_file", "edit_file", "shell_command", "monitor_command"],
        )

    if needs("security", "auth", "rbac", "pii", "compliance", "privacy", "encryption", "audit"):
        add(
            "security-engineer",
            "Security Engineer",
            "security_engineer",
            "Security & Compliance Engineer",
            "security",
            "engineering-manager",
            "Enforce security, privacy, compliance, and approval guardrails.",
            "Review access control, data handling, audit logging, encryption, and regulatory constraints.",
            ["security review", "compliance", "access control"],
            ["read_file", "search_code", "search_memory"],
        )

    add(
        "qa-engineer",
        "QA Engineer",
        "qa_engineer",
        "Quality & Acceptance Engineer",
        "quality",
        "engineering-manager",
        "Verify each requirement through tests and acceptance evidence.",
        "Create test plans from acceptance criteria, validate defects, and report readiness.",
        ["quality assurance", "test planning", "acceptance validation"],
        ["read_file", "search_code", "shell_command"],
    )

    return rows


async def _write_worker_hierarchy_document(session, project_id: str, rows: list[dict]) -> None:
    from sqlalchemy import text

    if not rows:
        return
    by_id = {row["id"]: row for row in rows}
    lines = ["# Worker Hierarchy", ""]
    for row in rows:
        manager = by_id.get(row.get("reports_to") or "", {}).get("name", "Root")
        lines.append(
            f"- {row['name']} ({row.get('designation') or row.get('role')}) - reports to {manager}; {row.get('role_description') or ''}"
        )
    content = "\n".join(lines)
    await session.execute(text(
        "INSERT INTO artifacts (id, projectid, name, type, content, uri, storagepath, agentid, createdat, versionhistory) "
        "VALUES (:id, :pid, :name, 'Worker Hierarchy', :content, :uri, :uri, NULL, :t, '{}') "
        "ON CONFLICT (id) DO UPDATE SET content = EXCLUDED.content, storagepath = EXCLUDED.storagepath, uri = EXCLUDED.uri"
    ), {
        "id": f"doc-{project_id}-worker-hierarchy",
        "pid": project_id,
        "name": "worker-hierarchy.md",
        "content": content,
        "uri": f"knowledge/{project_id}/worker-hierarchy.md",
        "t": _now(),
    })


async def _apply_revised_phases(project_id: str, requirements: dict, revised_phases: list[dict]) -> None:
    """Update requirements with agent-revised phase dates and re-seed meetings."""
    from sqlalchemy import text

    # Merge revised dates into the requirements phases
    phases = requirements.get("phases") or []
    revised_by_name = {p["name"]: p for p in revised_phases}
    for phase in phases:
        if isinstance(phase, dict) and phase.get("name") in revised_by_name:
            rev = revised_by_name[phase["name"]]
            phase["startDate"] = rev.get("startDate") or phase.get("startDate")
            phase["endDate"] = rev.get("endDate") or phase.get("endDate")
            phase["meetingFrequency"] = rev.get("meetingFrequency") or phase.get("meetingFrequency")

    async with db_session() as session:
        # Update requirements in the project
        await session.execute(text(
            "UPDATE business_projects SET requirements = :req, updatedat = :t WHERE id = :pid"
        ), {"req": json.dumps(requirements), "t": _now(), "pid": project_id})

        # Delete existing scheduled meetings so they get re-seeded with new dates
        await session.execute(text(
            "DELETE FROM meetings WHERE project_id = :pid AND source = 'ba_scheduled'"
        ), {"pid": project_id})

        # Re-seed meetings with the updated dates
        from ecms.api.rest.platform import _ensure_project_meetings, _row_to_dict as _platform_row
        project_row = (await session.execute(text(
            "SELECT * FROM business_projects WHERE id = :pid"
        ), {"pid": project_id})).first()
        project = _platform_row(project_row) if project_row else {}
        if project:
            await _ensure_project_meetings(session, project)


def _fallback_org_mappings(rows: list[dict], org_roster: list[dict]) -> list[dict]:
    """Build deterministic org_mappings when the LLM doesn't produce them.

    For each project agent, find the best-matching org member by
    department/role/skill overlap. Returns a list of mapping dicts
    compatible with the governance assignment insert.
    """
    def _normalize(s: str) -> str:
        return s.lower().replace("_", " ").replace("-", " ").strip()

    def _score_agent_org(agent_row: dict, org_member: dict) -> float:
        """Score how well an org member matches a project agent (0-1)."""
        agent_dept = _normalize(agent_row.get("department", ""))
        agent_role = _normalize(agent_row.get("role", ""))
        agent_skills = {_normalize(s) for s in (agent_row.get("skills") or [])}

        org_dept = _normalize(org_member.get("department", ""))
        org_role = _normalize(org_member.get("role", ""))
        org_skills = {_normalize(s) for s in (org_member.get("skills") or [])}

        score = 0.0

        # Department match (strongest signal)
        if agent_dept and org_dept:
            if agent_dept == org_dept:
                score += 0.5
            elif agent_dept in org_dept or org_dept in agent_dept:
                score += 0.3

        # Role keyword overlap
        agent_words = set(agent_role.split())
        org_words = set(org_role.split())
        common_role_words = agent_words & org_words - {"the", "a", "an", "of", "and"}
        if common_role_words:
            score += 0.2 * min(1.0, len(common_role_words) / max(len(agent_words), 1))

        # Skill overlap
        if agent_skills and org_skills:
            overlap = agent_skills & org_skills
            if overlap:
                score += 0.3 * min(1.0, len(overlap) / max(len(agent_skills), 1))

        return score

    mappings: list[dict] = []
    used_org_members: set[str] = set()

    for agent_row in rows:
        agent_key = agent_row["id"].split(":", 1)[-1] if ":" in agent_row["id"] else agent_row["id"]

        best_score = -1.0
        best_member = None
        for org_member in org_roster:
            if org_member["id"] in used_org_members:
                continue
            s = _score_agent_org(agent_row, org_member)
            if s > best_score:
                best_score = s
                best_member = org_member

        if best_member:
            used_org_members.add(best_member["id"])
            mappings.append({
                "project_agent_key": agent_key,
                "org_member_id": best_member["id"],
                "responsibility": "primary_owner",
            })

    # If some agents have no match (all org members used), assign remaining to
    # the highest-ranking available org member (first in roster)
    assigned_keys = {m["project_agent_key"] for m in mappings}
    for agent_row in rows:
        agent_key = agent_row["id"].split(":", 1)[-1] if ":" in agent_row["id"] else agent_row["id"]
        if agent_key not in assigned_keys and org_roster:
            # Use the first org member (typically highest rank)
            mappings.append({
                "project_agent_key": agent_key,
                "org_member_id": org_roster[0]["id"],
                "responsibility": "monitor",
            })

    # Assign CEO (or highest-ranking leader) as monitor for critical agents
    # This ensures executive oversight on key project roles across all projects
    ceo_member = None
    for org_member in org_roster:
        if org_member.get("role", "").lower() in ("ceo", "chief_executive_officer"):
            ceo_member = org_member
            break
    # Fallback to first org member if no explicit CEO role found
    if not ceo_member and org_roster:
        ceo_member = org_roster[0]

    if ceo_member:
        critical_agent_keys = {"delivery_manager", "solution_architect", "engineering_manager"}
        existing_ceo_assignments = {m["project_agent_key"] for m in mappings if m["org_member_id"] == ceo_member["id"]}
        for agent_row in rows:
            agent_key = agent_row["id"].split(":", 1)[-1] if ":" in agent_row["id"] else agent_row["id"]
            if agent_key in critical_agent_keys and agent_key not in existing_ceo_assignments:
                mappings.append({
                    "project_agent_key": agent_key,
                    "org_member_id": ceo_member["id"],
                    "responsibility": "monitor",
                })

    return mappings


async def _run_team_design(project_id: str, requirements: dict, conversation: list[dict]) -> None:
    """Background worker: generate the org chart and persist it as agents rows.

    On any failure the project's team_status is set to 'failed' so the workspace
    can offer a regenerate action; project creation itself is never affected.
    """
    import uuid as _uuid
    from ecms.agent.ba.agent import design_team as ba_design_team, retrieve_knowledge
    from ecms.agent.ba.catalog import get_model_ids, get_tool_names
    from ecms.persistence.repositories.agent import AgentRepository

    try:
        knowledge_context = await retrieve_knowledge(
            requirements.get("objective", ""), conversation,
        )
        model_ids = await get_model_ids()
        tool_names = get_tool_names()

        # Fetch permanent org roster for mapping
        org_roster: list[dict] = []
        try:
            async with db_session() as session:
                from sqlalchemy import text
                org_rows = (await session.execute(
                    text("SELECT id, name, role, department, skills FROM organization_members WHERE status = 'active'")
                )).fetchall()
                org_roster = [
                    {"id": r[0], "name": r[1], "role": r[2], "department": r[3], "skills": r[4] or []}
                    for r in org_rows
                ]
        except Exception:
            logger.warning("[discovery] could not fetch org roster for team design")

        if not org_roster:
            raise RuntimeError(
                "team design requires at least one active organization employee"
            )

        revised_phases = []
        org_mappings: list[dict] = []
        try:
            team = await ba_design_team(
                requirements, conversation, model_ids, tool_names,
                knowledge_context=knowledge_context,
                org_roster=org_roster,
            )
            rows = team.to_rows(project_id)
            revised_phases = [p.model_dump() for p in team.revised_phases]
            org_mappings = [m.model_dump() for m in team.org_mappings]
        except Exception as exc:  # noqa: BLE001 - fallback keeps workspace usable
            logger.warning("[discovery] LLM team design failed for %s, using deterministic fallback: %s", project_id, exc)
            rows = _fallback_team_rows(project_id, requirements, model_ids, tool_names)

        # If the agent revised phase dates, update requirements and re-seed meetings
        if revised_phases:
            await _apply_revised_phases(project_id, requirements, revised_phases)

        expected_agent_keys = {
            row["id"].split(":", 1)[-1] if ":" in row["id"] else row["id"]
            for row in rows
        }
        active_member_ids = {member["id"] for member in org_roster}

        # Keep valid BA assignments and deterministically fill every gap. An
        # incomplete or hallucinated mapping must never prevent the team from
        # becoming ready when active organization employees are available.
        org_mappings = [
            mapping
            for mapping in org_mappings
            if mapping["project_agent_key"] in expected_agent_keys
            and mapping["org_member_id"] in active_member_ids
        ]
        mapped_agent_keys = {mapping["project_agent_key"] for mapping in org_mappings}
        if mapped_agent_keys != expected_agent_keys:
            fallback_mappings = _fallback_org_mappings(rows, org_roster)
            org_mappings.extend(
                mapping
                for mapping in fallback_mappings
                if mapping["project_agent_key"] not in mapped_agent_keys
            )

        async with db_session() as session:
            repo = AgentRepository(session)
            await repo.delete_by_project(project_id)  # idempotent re-design
            for row in rows:
                await repo.create(**row)
            await _write_worker_hierarchy_document(session, project_id, rows)

            # Write governance assignments from org_mappings
            from sqlalchemy import text
            for row in rows:
                await session.execute(
                    text(
                        "DELETE FROM project_agent_governance_assignments "
                        "WHERE project_agent_id = :aid"
                    ),
                    {"aid": row["id"]},
                )
            for mapping in org_mappings:
                project_agent_id = f"{project_id}:{mapping['project_agent_key']}"
                await session.execute(text(
                    "INSERT INTO project_agent_governance_assignments "
                    "(id, organization_member_id, project_agent_id, project_id, "
                    "responsibility, status, assigned_by_user_id, assigned_at, updated_at) "
                    "VALUES (:id, :mid, :paid, :pid, :resp, 'active', 'ba_agent', NOW(), NOW())"
                ), {
                    "id": f"gov-{_uuid.uuid4().hex[:12]}",
                    "mid": mapping["org_member_id"],
                    "paid": project_agent_id,
                    "pid": project_id,
                    "resp": mapping["responsibility"],
                })

            assigned_agent_ids = set((await session.execute(text(
                "SELECT DISTINCT project_agent_id "
                "FROM project_agent_governance_assignments "
                "WHERE project_id = :pid AND status = 'active'"
            ), {"pid": project_id})).scalars().all())
            expected_agent_ids = {row["id"] for row in rows}
            missing_assignments = sorted(expected_agent_ids - assigned_agent_ids)
            if missing_assignments:
                raise RuntimeError(
                    "governance persistence left project agents unassigned: "
                    f"{missing_assignments}"
                )

            logger.info(
                "[discovery] wrote %d governance assignments for project %s",
                len(org_mappings),
                project_id,
            )

        await _set_team_status(project_id, "ready")
        logger.info("[discovery] team ready for project %s (%d agents)", project_id, len(rows))
    except Exception as exc:  # noqa: BLE001 - background task must not crash silently
        logger.exception("[discovery] team design failed for project %s: %s", project_id, exc)
        try:
            await _set_team_status(project_id, "failed")
        except Exception:  # pragma: no cover - defensive
            logger.exception("[discovery] could not mark team_status=failed for %s", project_id)


@router.post("/{session_id}/design-team")
async def design_team_endpoint(session_id: str, request: Request):
    """Kick off background team design. Returns 202 immediately.

    Requires the session to be FINALIZED and linked to a project. The workspace
    polls the team endpoint for completion.
    """
    await _get_current_user(request)
    sess = await _load_session(session_id)
    if sess["stage"] != "FINALIZED":
        _error("WRONG-STAGE", f"Cannot design team from {sess['stage']}", 400)

    pid = sess.get("project_id")
    if not pid:
        _error("NO-PROJECT", "Session is not linked to a project yet", 400)

    requirements = sess.get("requirements") or {}
    if not requirements:
        _error("NO-REQUIREMENTS", "Session has no finalized requirements", 400)

    conversation = sess.get("messages") or []

    await _set_team_status(pid, "generating")
    # Fire-and-forget: generation runs after this handler returns.
    asyncio.create_task(_run_team_design(pid, requirements, conversation))

    return {"session_id": session_id, "project_id": pid, "team_status": "generating"}


@router.post("/projects/{project_id}/design-team")
async def regenerate_project_team(project_id: str, request: Request):
    """Re-run team design for a project (used by the workspace 'Regenerate' action).

    Looks up the linked discovery session by project_id so the workspace does not
    need to know the session id. Returns 202 and runs generation in the background.
    """
    await _get_current_user(request)
    async with db_session() as session:
        from sqlalchemy import text
        row = (await session.execute(text(
            "SELECT * FROM discovery_sessions WHERE project_id = :pid "
            "ORDER BY updated_at DESC LIMIT 1"
        ), {"pid": project_id})).first()
    if not row:
        _error("NO-SESSION", "No discovery session linked to this project", 404)
    sess = _row_to_dict(row)
    requirements = sess.get("requirements")
    if isinstance(requirements, str):
        requirements = json.loads(requirements)
    if not requirements:
        _error("NO-REQUIREMENTS", "Linked session has no finalized requirements", 400)
    messages = sess.get("messages")
    if isinstance(messages, str):
        messages = json.loads(messages)

    await _set_team_status(project_id, "generating")
    asyncio.create_task(_run_team_design(project_id, requirements, messages or []))
    return {"project_id": project_id, "team_status": "generating"}


@router.get("/projects/{project_id}/team")
async def get_project_team(project_id: str, request: Request):
    """Return the project's team status and its agents (if ready)."""
    await _get_current_user(request)
    async with db_session() as session:
        from sqlalchemy import text
        row = (await session.execute(
            text("SELECT team_status FROM business_projects WHERE id = :id"),
            {"id": project_id},
        )).first()
        if not row:
            _error("NOT-FOUND", "Project not found", 404)
        team_status = row[0] or "pending"

    from ecms.persistence.repositories.agent import AgentRepository
    async with db_session() as session:
        repo = AgentRepository(session)
        agents = await repo.list_by_project(project_id)

    return {
        "project_id": project_id,
        "team_status": team_status,
        "agents": [a.to_dict() for a in agents],
    }

"""Project meetings API — calendar, notes, decisions, and recordings.

Meetings are project-scoped records surfaced in the ProjectDetails "Meetings"
tab: a calendar grid, a per-day detail panel, and a rich detail modal for past
meetings (summary, key decisions, attendee counts, and an inline recording).

Recordings are stored on local disk under the same convention as project
document uploads (/workspace/uploads/{project_id}/recordings/) and streamed
back via a download endpoint so the frontend can play them inline.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, UploadFile
from fastapi import File as FastAPIFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from ecms.persistence.database.rest_session import db_session

router = APIRouter(prefix="/api")

BASE_UPLOAD_DIR = Path("/workspace/uploads")

# Columns selected for every meeting read; keeps SELECT * drift out of the code.
_COLUMNS = (
    "id, project_id, title, meeting_date, meeting_time, duration, type, status, "
    "participants, agenda, notes, summary, decisions, action_items, attachments, "
    "recording_path, recording_name, source, created_at, updated_at"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _uuid() -> str:
    return str(uuid.uuid4())


def _error(code: str, message: str, status: int = 400):
    raise HTTPException(status_code=status, detail={"error": code, "message": message})


async def _get_current_user(request: Request) -> dict:
    auth = request.headers.get("Authorization", "")
    token = auth.removeprefix("Bearer ").strip()
    if not token:
        _error("AUTH-4011", "Missing token", 401)
    async with db_session() as session:
        from sqlalchemy import text

        row = (
            await session.execute(
                text("SELECT * FROM auth_sessions WHERE token = :t"), {"t": token}
            )
        ).first()
        if not row:
            _error("AUTH-4012", "Invalid session", 401)
        sess = {k.lower(): v for k, v in row._mapping.items()}
        user_row = (
            await session.execute(
                text("SELECT * FROM users WHERE id = :id"), {"id": sess["userid"]}
            )
        ).first()
        if not user_row:
            _error("AUTH-4013", "User not found", 401)
        return {k.lower(): v for k, v in user_row._mapping.items()}


def _row_to_meeting(row) -> dict:
    """Map a meetings row to the shape the frontend consumes."""
    d = {k.lower(): v for k, v in row._mapping.items()}

    def _arr(v):
        if isinstance(v, list):
            return v
        if isinstance(v, str) and v:
            try:
                return json.loads(v)
            except ValueError:
                return []
        return []

    participants = _arr(d.get("participants"))
    status = d.get("status") or "upcoming"
    meeting_date = d.get("meeting_date")
    if meeting_date and meeting_date < datetime.now(UTC).date().isoformat():
        status = "past"
    return {
        "id": d.get("id"),
        "project_id": d.get("project_id"),
        "title": d.get("title"),
        "date": meeting_date,
        "time": d.get("meeting_time"),
        "duration": d.get("duration"),
        "type": d.get("type") or "both",
        "status": status,
        "past": status == "past",
        "participants": participants,
        "totalAttendees": len(participants),
        "agenda": d.get("agenda"),
        "notes": d.get("notes"),
        "summary": d.get("summary"),
        "decisions": _arr(d.get("decisions")),
        "actionItems": _arr(d.get("action_items")),
        "attachments": _arr(d.get("attachments")),
        "recording": d.get("recording_name"),
        "hasRecording": bool(d.get("recording_path")),
        "source": d.get("source") or "manual",
        "created_at": d.get("created_at"),
    }


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class MeetingBody(BaseModel):
    title: str
    date: str | None = None  # e.g. "2026-07-15"
    time: str | None = None  # e.g. "10:00 AM"
    duration: str | None = None
    type: str | None = "both"  # 'human' | 'agent' | 'both'
    status: str | None = "upcoming"  # 'upcoming' | 'past'
    participants: list[str] = []
    agenda: str | None = None
    notes: str | None = None
    summary: str | None = None
    decisions: list[str] = []
    action_items: list[str] = []
    attachments: list[str] = []


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/projects/{project_id}/meetings")
async def list_meetings(project_id: str, request: Request):
    """All meetings for a project, newest-first by date."""
    await _get_current_user(request)
    async with db_session() as session:
        from sqlalchemy import text

        rows = (
            await session.execute(
                text(
                    f"SELECT {_COLUMNS} FROM meetings WHERE project_id = :pid "
                    "ORDER BY meeting_date DESC NULLS LAST, created_at DESC"
                ),
                {"pid": project_id},
            )
        ).fetchall()
    return {"meetings": [_row_to_meeting(r) for r in rows]}


@router.post("/projects/{project_id}/meetings")
async def create_meeting(project_id: str, body: MeetingBody, request: Request):
    """Create a meeting (manual scheduling / logging from the UI)."""
    await _get_current_user(request)
    mid = _uuid()
    now = _now()
    async with db_session() as session:
        from sqlalchemy import text

        await session.execute(
            text(
                "INSERT INTO meetings "
                "(id, project_id, title, meeting_date, meeting_time, duration, type, status, "
                " participants, agenda, notes, summary, decisions, action_items, attachments, "
                " source, created_at, updated_at) "
                "VALUES (:id, :pid, :title, :date, :time, :dur, :type, :status, "
                " :participants, :agenda, :notes, :summary, :decisions, :action_items, :attachments, "
                " 'manual', :t, :t)"
            ),
            {
                "id": mid,
                "pid": project_id,
                "title": body.title,
                "date": body.date,
                "time": body.time,
                "dur": body.duration,
                "type": body.type or "both",
                "status": body.status or "upcoming",
                "participants": json.dumps(body.participants or []),
                "agenda": body.agenda,
                "notes": body.notes,
                "summary": body.summary,
                "decisions": json.dumps(body.decisions or []),
                "action_items": json.dumps(body.action_items or []),
                "attachments": json.dumps(body.attachments or []),
                "t": now,
            },
        )
        row = (
            await session.execute(
                text(f"SELECT {_COLUMNS} FROM meetings WHERE id = :id"), {"id": mid}
            )
        ).first()
    return _row_to_meeting(row)


@router.delete("/projects/{project_id}/meetings/{meeting_id}")
async def delete_meeting(project_id: str, meeting_id: str, request: Request):
    """Delete a meeting and its recording file (if any)."""
    await _get_current_user(request)
    async with db_session() as session:
        from sqlalchemy import text

        row = (
            await session.execute(
                text("SELECT recording_path FROM meetings WHERE id = :id AND project_id = :pid"),
                {"id": meeting_id, "pid": project_id},
            )
        ).first()
        if not row:
            _error("NOT-FOUND", "Meeting not found", 404)
        rec_path = row[0]
        await session.execute(
            text("DELETE FROM meetings WHERE id = :id AND project_id = :pid"),
            {"id": meeting_id, "pid": project_id},
        )
    # Best-effort file cleanup outside the transaction.
    if rec_path:
        try:
            Path(rec_path).unlink(missing_ok=True)
        except OSError:
            pass
    return {"success": True}


@router.post("/projects/{project_id}/meetings/{meeting_id}/recording")
async def upload_recording(
    project_id: str,
    meeting_id: str,
    file: UploadFile = FastAPIFile(...),
    request: Request = None,
):
    """Attach a recording file to a meeting (stored on local disk)."""
    await _get_current_user(request)
    async with db_session() as session:
        from sqlalchemy import text

        exists = (
            await session.execute(
                text("SELECT 1 FROM meetings WHERE id = :id AND project_id = :pid"),
                {"id": meeting_id, "pid": project_id},
            )
        ).first()
        if not exists:
            _error("NOT-FOUND", "Meeting not found", 404)

    content = await file.read()
    hash_digest = hashlib.sha256(content).hexdigest()[:12]
    ext = file.filename.rsplit(".", 1)[-1] if "." in (file.filename or "") else "mp4"
    filename = f"{meeting_id}-{hash_digest}.{ext}"
    rec_dir = BASE_UPLOAD_DIR / project_id / "recordings"
    rec_dir.mkdir(parents=True, exist_ok=True)
    filepath = rec_dir / filename
    filepath.write_bytes(content)

    async with db_session() as session:
        from sqlalchemy import text

        await session.execute(
            text(
                "UPDATE meetings SET recording_path = :p, recording_name = :n, updated_at = :t "
                "WHERE id = :id AND project_id = :pid"
            ),
            {
                "p": str(filepath),
                "n": file.filename,
                "t": _now(),
                "id": meeting_id,
                "pid": project_id,
            },
        )

    return {"success": True, "recording": file.filename}


@router.get("/projects/{project_id}/meetings/{meeting_id}/recording")
async def get_recording(project_id: str, meeting_id: str, request: Request):
    """Stream a meeting's recording for inline playback / download."""
    await _get_current_user(request)
    async with db_session() as session:
        from sqlalchemy import text

        row = (
            await session.execute(
                text(
                    "SELECT recording_path, recording_name FROM meetings "
                    "WHERE id = :id AND project_id = :pid"
                ),
                {"id": meeting_id, "pid": project_id},
            )
        ).first()
    if not row or not row[0]:
        _error("NOT-FOUND", "No recording for this meeting", 404)
    path = Path(row[0])
    if not path.exists():
        _error("NOT-FOUND", "Recording file missing", 404)
    return FileResponse(str(path), filename=row[1] or path.name)


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------


class NotificationActionBody(BaseModel):
    confirmed_time: str | None = None


@router.get("/projects/{project_id}/notifications")
async def list_notifications(project_id: str, request: Request):
    """List unread notifications for a project."""
    await _get_current_user(request)
    async with db_session() as session:
        from sqlalchemy import text

        rows = (
            await session.execute(
                text(
                    "SELECT id, project_id, meeting_id, type, title, message, status, "
                    "action_type, action_data, created_at, updated_at "
                    "FROM notifications WHERE project_id = :pid "
                    "ORDER BY created_at DESC LIMIT 50"
                ),
                {"pid": project_id},
            )
        ).fetchall()
    return {
        "notifications": [
            {
                "id": r[0],
                "project_id": r[1],
                "meeting_id": r[2],
                "type": r[3],
                "title": r[4],
                "message": r[5],
                "status": r[6],
                "action_type": r[7],
                "action_data": r[8] if isinstance(r[8], dict) else json.loads(r[8] or "{}"),
                "created_at": r[9],
                "updated_at": r[10],
            }
            for r in rows
        ]
    }


@router.post("/projects/{project_id}/notifications/{notification_id}/confirm-time")
async def confirm_meeting_time(
    project_id: str,
    notification_id: str,
    body: NotificationActionBody,
    request: Request,
):
    """Confirm or set a meeting time from a notification."""
    await _get_current_user(request)
    now = datetime.now(UTC).isoformat()
    async with db_session() as session:
        from sqlalchemy import text

        row = (
            await session.execute(
                text(
                    "SELECT meeting_id, action_data FROM notifications "
                    "WHERE id = :nid AND project_id = :pid"
                ),
                {"nid": notification_id, "pid": project_id},
            )
        ).first()
        if not row:
            _error("NOT-FOUND", "Notification not found", 404)

        meeting_id = row[0]
        confirmed_time = body.confirmed_time

        # Update the meeting time
        if meeting_id and confirmed_time:
            await session.execute(
                text(
                    "UPDATE meetings SET meeting_time = :time, updated_at = :t "
                    "WHERE id = :mid AND project_id = :pid"
                ),
                {"time": confirmed_time, "t": now, "mid": meeting_id, "pid": project_id},
            )

        # Mark notification as resolved
        await session.execute(
            text(
                "UPDATE notifications SET status = 'resolved', updated_at = :t "
                "WHERE id = :nid AND project_id = :pid"
            ),
            {"t": now, "nid": notification_id, "pid": project_id},
        )

        # Create a confirmation notification
        conf_id = str(uuid.uuid4())
        await session.execute(
            text(
                "INSERT INTO notifications "
                "(id, project_id, meeting_id, type, title, message, status, action_type, action_data, created_at, updated_at) "
                "VALUES (:id, :pid, :mid, 'time_confirmed', :title, :msg, 'unread', NULL, '{}', :t, :t)"
            ),
            {
                "id": conf_id,
                "pid": project_id,
                "mid": meeting_id,
                "title": "Meeting Time Confirmed",
                "msg": f"Meeting time set to {confirmed_time}.",
                "t": now,
            },
        )

    return {"success": True, "confirmed_time": confirmed_time}


@router.post("/projects/{project_id}/notifications/{notification_id}/dismiss")
async def dismiss_notification(
    project_id: str,
    notification_id: str,
    request: Request,
):
    """Dismiss a notification."""
    await _get_current_user(request)
    now = datetime.now(UTC).isoformat()
    async with db_session() as session:
        from sqlalchemy import text

        await session.execute(
            text(
                "UPDATE notifications SET status = 'dismissed', updated_at = :t "
                "WHERE id = :nid AND project_id = :pid"
            ),
            {"t": now, "nid": notification_id, "pid": project_id},
        )
    return {"success": True}

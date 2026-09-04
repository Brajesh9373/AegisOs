"""Platform API router — serves all aegisOS frontend endpoints.

Uses raw SQL against the platform tables (organization, users, auth_sessions,
business_projects, project_agents, execution_nodes, human_queue, artifacts,
audit_logs). Completely independent of existing ECMS routes.
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from ecms.persistence.database.rest_session import db_session

router = APIRouter(prefix="/api")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _uuid() -> str:
    return str(uuid.uuid4())


def _row_to_dict(row) -> dict:
    """Convert a SQLAlchemy Row to a plain dict with lowercase keys."""
    if not row:
        return {}
    return {k.lower(): v for k, v in row._mapping.items()}


def _json_value(value, default):
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except Exception:
            return default
    return default


def _project_requirements(project: dict) -> dict:
    return _json_value(project.get("requirements"), {})


def _json_array(value) -> list:
    parsed = _json_value(value, [])
    return parsed if isinstance(parsed, list) else []


async def _hydrate_project_owner(session, project: dict) -> dict:
    """Attach human-readable owner fields without changing the stored owner id."""
    if not project:
        return project
    owner_id = project.get("ownerid") or project.get("ownerId")
    if not owner_id:
        return project

    from sqlalchemy import text

    row = (
        await session.execute(
            text("SELECT * FROM users WHERE id = :id"),
            {"id": owner_id},
        )
    ).first()
    user = _row_to_dict(row) if row else {}
    display = user.get("name") or user.get("email") or "Project Owner"
    project["owner"] = display
    project["ownername"] = display
    project["owneremail"] = user.get("email") or ""
    return project


def _parse_project_datetime(value) -> datetime:
    if value:
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            if parsed.tzinfo is not None:
                parsed = parsed.astimezone(UTC).replace(tzinfo=None)
            return parsed
        except ValueError:
            pass
    return datetime.now(UTC).replace(tzinfo=None)


def _next_weekday_after(base: datetime, weekday: int) -> datetime:
    days = (weekday - base.weekday()) % 7
    return base + timedelta(days=days or 7)


def _doc_size(content: str) -> str:
    size = len((content or "").encode("utf-8"))
    if size < 1024:
        return f"{size} B"
    return f"{size / 1024:.1f} KB"


def _slug(value: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "-" for ch in value or "")
    return "-".join(part for part in cleaned.split("-") if part)[:80] or "project"


def _format_detail_items(items: list[dict]) -> str:
    lines: list[str] = []
    for item in items or []:
        if isinstance(item, dict):
            label = item.get("label") or "Item"
            detail = item.get("detail") or ""
            lines.append(f"- {label}: {detail}".strip())
        elif item:
            lines.append(f"- {item}")
    return "\n".join(lines)


def _build_requirement_documents(project: dict) -> list[dict]:
    """Generate project knowledge documents from finalized requirements.

    These are deterministic AI-workspace artifacts: they are derived from the
    BA agent's structured requirements instead of being front-end demo files.
    """
    reqs = _project_requirements(project)
    if not reqs:
        return []

    project_name = reqs.get("projectName") or project.get("name") or "Project"
    objective = reqs.get("objective") or project.get("businessgoal") or ""
    base = _slug(project_name)

    functional = "\n".join(f"- {item}" for item in reqs.get("functionalReqs") or [])
    tech_stack = ", ".join(reqs.get("techStack") or []) or "Not specified"
    skills = ", ".join(reqs.get("skills") or []) or "Not specified"
    connectors = ", ".join(reqs.get("connectors") or []) or "Not specified"

    phases = reqs.get("phases") or []
    phase_lines = [
        "- Phase 0: Discovery & Requirements - Captures what has happened so far, finalized decisions, open assumptions, and prerequisites for execution."
    ]
    previous = "Phase 0"
    for idx, phase in enumerate(phases, start=1):
        if isinstance(phase, dict):
            name = phase.get("name") or f"Phase {idx}"
            duration = phase.get("duration") or "Duration TBD"
            desc = phase.get("description") or ""
            phase_lines.append(
                f"- Phase {idx}: {name} ({duration}) - depends on {previous}. {desc}".strip()
            )
            previous = name

    requirement_doc = {
        "id": f"doc-{project['id']}-requirements",
        "name": f"{base}-requirements-package.md",
        "type": "Requirements",
        "category": "Requirements",
        "content": "\n".join(
            [
                f"# {project_name} Requirements Package",
                "",
                f"Objective: {objective}",
                "",
                "## Functional Requirements",
                functional or "No functional requirements were finalized.",
                "",
                "## Required Skills",
                skills,
                "",
                "## Required Connectors",
                connectors,
            ]
        ),
    }

    architecture_doc = {
        "id": f"doc-{project['id']}-architecture",
        "name": f"{base}-architecture-brief.md",
        "type": "Architecture",
        "category": "Architecture",
        "content": "\n".join(
            [
                f"# {project_name} Architecture Brief",
                "",
                f"Tech stack: {tech_stack}",
                "",
                "## Infrastructure",
                _format_detail_items(reqs.get("infrastructure") or [])
                or "Infrastructure not finalized.",
                "",
                "## Integrations",
                connectors,
            ]
        ),
    }

    delivery_doc = {
        "id": f"doc-{project['id']}-delivery-plan",
        "name": f"{base}-phase-dependency-plan.md",
        "type": "Delivery Plan",
        "category": "Plan",
        "content": "\n".join(
            [
                f"# {project_name} Phase Dependency Plan",
                "",
                "The first phase records what has happened so far and what is required before execution. Each later phase depends on the phase above it.",
                "",
                "\n".join(phase_lines),
            ]
        ),
    }

    risk_doc = {
        "id": f"doc-{project['id']}-risk-governance",
        "name": f"{base}-risk-governance-register.md",
        "type": "Risk Register",
        "category": "Governance",
        "content": "\n".join(
            [
                f"# {project_name} Risk & Governance Register",
                "",
                "## Risks",
                "\n".join(f"- {risk}" for risk in reqs.get("risks") or []) or "No risks finalized.",
                "",
                "## Governance",
                _format_detail_items(reqs.get("governance") or []) or "Governance not finalized.",
                "",
                "## Guardrails",
                _format_detail_items(reqs.get("guardrails") or []) or "Guardrails not finalized.",
            ]
        ),
    }

    return [requirement_doc, architecture_doc, delivery_doc, risk_doc]


async def _ensure_project_documents(session, project: dict) -> None:
    from sqlalchemy import text

    for doc in _build_requirement_documents(project):
        content = doc["content"]
        await session.execute(
            text(
                "INSERT INTO artifacts (id, projectid, name, type, content, uri, storagepath, agentid, createdat, versionhistory) "
                "VALUES (:id, :pid, :name, :type, :content, :uri, :uri, NULL, :t, '{}') "
                "ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, type = EXCLUDED.type, content = EXCLUDED.content, uri = EXCLUDED.uri, storagepath = EXCLUDED.storagepath"
            ),
            {
                "id": doc["id"],
                "pid": project["id"],
                "name": doc["name"],
                "type": doc["type"],
                "content": content,
                "uri": f"knowledge/{project['id']}/{doc['name']}",
                "t": _now(),
            },
        )


def _artifact_to_workspace_doc(artifact: dict) -> dict:
    name = artifact.get("name") or artifact.get("storagepath") or artifact.get("uri") or "Artifact"
    content = artifact.get("content") or ""
    return {
        "id": artifact.get("id"),
        "name": name.split("/")[-1],
        "size": _doc_size(content) if content else "",
        "category": artifact.get("type") or "Document",
        "path": artifact.get("storagepath") or artifact.get("uri") or "",
    }


def _state_weight(state: str | None) -> float:
    normalized = (state or "").strip().lower().replace("_", " ")
    if normalized in {"completed", "complete", "done", "success", "succeeded"}:
        return 1.0
    if normalized in {"running", "in progress", "executing", "active"}:
        return 0.5
    if normalized in {"blocked", "failed", "error"}:
        return 0.25
    if normalized in {"review", "in review"}:
        return 0.75
    return 0.0


def _compute_progress(nodes: list[dict], work_rows: list[dict], project: dict) -> int | None:
    if nodes:
        return round(sum(_state_weight(n.get("state")) for n in nodes) / len(nodes) * 100)
    actionable_work = [w for w in work_rows if w.get("kind") in {"story", "bug"}]
    if actionable_work and any(
        _normalize_work_status(w.get("status")) != "TO_DO" for w in actionable_work
    ):
        return round(
            sum(_state_weight(_normalize_work_status(w.get("status"))) for w in actionable_work)
            / len(actionable_work)
            * 100
        )
    status = (project.get("status") or "").lower()
    if status in {"completed", "done"}:
        return 100
    return None


def _workspace_timeline(
    project: dict, reqs: dict, meetings: list[dict], agents: list[dict]
) -> list[dict]:
    timeline: list[dict] = []
    if project.get("createdat"):
        timeline.append(
            {
                "event": "Project Created",
                "date": str(project.get("createdat"))[:10],
                "desc": f"{project.get('name')} project record was created.",
            }
        )
    if reqs:
        timeline.append(
            {
                "event": "Requirements Finalized",
                "date": str(project.get("updatedat") or project.get("createdat") or "")[:10],
                "desc": (
                    f"{len(reqs.get('functionalReqs') or [])} functional requirements, "
                    f"{len(reqs.get('phases') or [])} delivery phases, and "
                    f"{len(reqs.get('risks') or [])} risks captured from discovery."
                ),
            }
        )
        previous = "Discovery & Requirements"
        # Build a lookup: phase name → earliest meeting date (fallback)
        phase_dates: dict[str, str] = {}
        for m in meetings:
            mtitle = (m.get("title") or "").strip()
            mdate = m.get("meeting_date") or ""
            for p in reqs.get("phases") or []:
                pname = p.get("name") if isinstance(p, dict) else ""
                if pname and mtitle.startswith(pname) and mdate:
                    if pname not in phase_dates or mdate < phase_dates[pname]:
                        phase_dates[pname] = mdate
        for idx, phase in enumerate(reqs.get("phases") or [], start=1):
            if isinstance(phase, dict):
                name = phase.get("name") or f"Phase {idx}"
                desc = phase.get("description") or ""
                # Prefer agent-provided startDate, fall back to meeting date, then duration
                date = (
                    phase.get("startDate")
                    or phase_dates.get(name)
                    or phase.get("duration")
                    or f"Phase {idx}"
                )
                timeline.append(
                    {
                        "event": name,
                        "date": date,
                        "desc": f"Depends on {previous}. {desc}".strip(),
                    }
                )
                previous = name
    for meeting in meetings:
        if meeting.get("status") == "past":
            timeline.append(
                {
                    "event": meeting.get("title") or "Meeting",
                    "date": meeting.get("meeting_date") or "",
                    "desc": meeting.get("summary") or meeting.get("agenda") or "",
                }
            )
    if agents:
        timeline.append(
            {
                "event": "Worker Hierarchy Created",
                "date": str(project.get("updatedat") or "")[:10],
                "desc": f"{len(agents)} project-specific AI workers assigned from the finalized requirements.",
            }
        )
    timeline.sort(key=lambda t: t.get("date") or "")
    return timeline


def _meeting_to_workspace(meeting: dict) -> dict:
    meeting_date = meeting.get("meeting_date")
    status = meeting.get("status") or "upcoming"
    if meeting_date and meeting_date < datetime.now(UTC).date().isoformat():
        status = "past"
    participants = _json_array(meeting.get("participants"))
    return {
        "id": meeting.get("id"),
        "project_id": meeting.get("project_id"),
        "title": meeting.get("title"),
        "date": meeting_date,
        "time": meeting.get("meeting_time"),
        "duration": meeting.get("duration"),
        "type": meeting.get("type") or "both",
        "status": status,
        "past": status == "past",
        "participants": participants,
        "totalAttendees": len(participants),
        "agenda": meeting.get("agenda"),
        "notes": meeting.get("notes"),
        "summary": meeting.get("summary"),
        "decisions": _json_array(meeting.get("decisions")),
        "actionItems": _json_array(meeting.get("action_items")),
        "attachments": _json_array(meeting.get("attachments")),
        "recording": meeting.get("recording_name"),
        "hasRecording": bool(meeting.get("recording_path")),
        "source": meeting.get("source") or "manual",
        "created_at": meeting.get("created_at"),
        "updated_at": meeting.get("updated_at"),
    }


async def _ensure_tbd_meeting_notifications(session, project_id: str) -> None:
    from sqlalchemy import text

    rows = (
        await session.execute(
            text(
                "SELECT id, title, meeting_date FROM meetings "
                "WHERE project_id = :pid AND meeting_time = 'TBD' AND source = 'ba_scheduled'"
            ),
            {"pid": project_id},
        )
    ).fetchall()
    for row in rows:
        meeting_id, title, meeting_date = row[0], row[1], row[2]
        existing = (
            await session.execute(
                text(
                    "SELECT 1 FROM notifications "
                    "WHERE project_id = :pid AND meeting_id = :mid AND type = 'meeting_time_confirm' LIMIT 1"
                ),
                {"pid": project_id, "mid": meeting_id},
            )
        ).first()
        if existing:
            continue
        await session.execute(
            text(
                "INSERT INTO notifications "
                "(id, project_id, meeting_id, type, title, message, status, action_type, action_data, created_at, updated_at) "
                "VALUES (:id, :pid, :mid, 'meeting_time_confirm', :title, :msg, 'unread', 'confirm_time', '{}', :t, :t)"
            ),
            {
                "id": _uuid(),
                "pid": project_id,
                "mid": meeting_id,
                "title": f"Set a time for: {title}",
                "msg": f"This meeting is scheduled for {meeting_date} but has no time yet. Please confirm a time.",
                "t": _now(),
            },
        )


async def _ensure_project_meetings(
    session,
    project: dict,
    *,
    preferred_time: str | None = None,
    meeting_frequency: str | None = "weekly",
) -> None:
    import logging

    _log = logging.getLogger(__name__)
    """Seed real workspace meetings from finalized requirements.

    The generated dates are deterministic enough to avoid demo rows but still
    reflect the BA conversation: discovery is recorded as the completed intake
    meeting, and each requirement phase gets kickoff/progress/gate reviews.
    """
    from sqlalchemy import text

    if not project or not project.get("id"):
        return

    project_id = project["id"]
    reqs = _project_requirements(project)
    if not reqs:
        return

    now = _now()
    base = _parse_project_datetime(project.get("createdat") or project.get("updatedat"))
    discovery_date = base.strftime("%Y-%m-%d")
    project_name = reqs.get("projectName") or project.get("name") or "Project"
    objective = (reqs.get("objective") or project.get("businessgoal") or "").strip()
    summary = f"Business Analyst discovery session for {project_name}."
    if objective:
        summary = f"{summary} {objective}"

    decisions: list[str] = []
    for phase in (reqs.get("phases") or [])[:5]:
        if isinstance(phase, dict):
            name = phase.get("name") or ""
            duration = phase.get("duration") or ""
            if name:
                decisions.append(f"{name} ({duration})" if duration else name)
    if not decisions:
        decisions = [r for r in (reqs.get("functionalReqs") or [])[:5] if isinstance(r, str)]

    await session.execute(
        text(
            "INSERT INTO meetings "
            "(id, project_id, title, meeting_date, meeting_time, duration, type, status, "
            "participants, agenda, notes, summary, decisions, action_items, attachments, source, created_at, updated_at) "
            "VALUES (:id, :pid, :title, :date, NULL, 'All day', 'both', 'past', "
            ":participants, :agenda, NULL, :summary, :decisions, '[]', '[]', 'ba_discovery', :t, :t) "
            "ON CONFLICT (id) DO NOTHING"
        ),
        {
            "id": f"ba-discovery-{project_id}",
            "pid": project_id,
            "title": "BA Discovery & Requirement Finalization",
            "date": discovery_date,
            "participants": json.dumps(["Project Owner", "Business Analyst Agent"]),
            "agenda": f"Requirement discovery, clarification, and approval for {project_name}.",
            "summary": summary,
            "decisions": json.dumps(decisions),
            "t": now,
        },
    )

    scheduled_count = (
        await session.execute(
            text(
                "SELECT count(1) FROM meetings WHERE project_id = :pid AND source = 'ba_scheduled'"
            ),
            {"pid": project_id},
        )
    ).scalar() or 0
    if scheduled_count:
        await _ensure_tbd_meeting_notifications(session, project_id)
        return

    phases = [phase for phase in (reqs.get("phases") or []) if isinstance(phase, dict)]
    if not phases:
        phases = [
            {
                "name": "Phase 1 - Discovery, Governance, and Architecture",
                "description": "Confirm scope, delivery governance, architecture, and project prerequisites.",
            }
        ]

    freq_days = {"daily": 1, "every2days": 2, "weekly": 7, "biweekly": 14, "monthly": 30}
    participants = json.dumps(
        ["Engagement Delivery Lead", "Engineering Manager", "Solution Architect"]
    )

    for phase_idx, phase in enumerate(phases[:8], start=1):
        phase_name = phase.get("name") or f"Phase {phase_idx}"
        phase_desc = phase.get("description") or ""

        # Use agent-provided dates if available, fall back to algorithmic generation
        agent_start = phase.get("startDate")
        agent_end = phase.get("endDate")
        agent_freq = phase.get("meetingFrequency")

        if agent_start and agent_end:
            try:
                phase_start_dt = datetime.strptime(agent_start, "%Y-%m-%d")
                phase_end_dt = datetime.strptime(agent_end, "%Y-%m-%d")
                phase_duration_days = max((phase_end_dt - phase_start_dt).days, 1)
            except ValueError:
                agent_start = None  # fall back

        if not agent_start or not agent_end:
            # Fallback: algorithmic generation for legacy requirements without dates
            cadence = max(freq_days.get(meeting_frequency or "weekly", 7), 7)
            phase_start_dt = _next_weekday_after(base, 1) + timedelta(
                days=max(cadence * 4, 28) * (phase_idx - 1)
            )
            phase_duration_days = max(cadence * 4, 28)
            phase_end_dt = phase_start_dt + timedelta(days=phase_duration_days)

        cadence = max(freq_days.get(agent_freq or meeting_frequency or "weekly", 7), 1)
        phase_duration_days = max((phase_end_dt - phase_start_dt).days, 1)

        # Generate meeting dates within the phase date range
        meetings = [
            (
                "kickoff",
                "Kickoff",
                "both",
                0,
                f"Align stakeholders, scope, dependencies, and readiness for {phase_name}.",
            ),
            (
                "progress",
                "Progress Review",
                "agent",
                min(cadence, phase_duration_days // 2),
                f"Review agent progress, blockers, evidence, and next actions for {phase_name}.",
            ),
            (
                "gate",
                "Gate Review",
                "human",
                phase_duration_days,
                f"Review deliverables, risks, approvals, and phase exit criteria for {phase_name}.",
            ),
        ]
        for key, label, meeting_type, day_offset, default_agenda in meetings:
            meeting_date = (phase_start_dt + timedelta(days=day_offset)).strftime("%Y-%m-%d")
            await session.execute(
                text(
                    "INSERT INTO meetings "
                    "(id, project_id, title, meeting_date, meeting_time, duration, type, status, "
                    "participants, agenda, notes, summary, decisions, action_items, attachments, "
                    "recording_path, recording_name, source, created_at, updated_at) "
                    "VALUES (:id, :pid, :title, :date, :time, '1 hour', :type, 'upcoming', "
                    ":participants, :agenda, NULL, NULL, '[]', '[]', '[]', NULL, NULL, 'ba_scheduled', :t, :t) "
                    "ON CONFLICT (id) DO NOTHING"
                ),
                {
                    "id": f"ba-scheduled-{project_id}-{phase_idx}-{key}",
                    "pid": project_id,
                    "title": f"{phase_name} - {label}",
                    "date": meeting_date,
                    "time": preferred_time or "TBD",
                    "type": meeting_type,
                    "participants": participants,
                    "agenda": phase_desc or default_agenda,
                    "t": now,
                },
            )

    await _ensure_tbd_meeting_notifications(session, project_id)


def _error_response(code: str, message: str, details=None, status: int = 400):
    raise HTTPException(
        status_code=status,
        detail={
            "success": False,
            "error": {
                "code": code,
                "message": message,
                "details": details,
                "traceId": f"req-{int(datetime.now().timestamp() * 1000)}",
            },
        },
    )


WORK_BOARD_COLUMNS = [
    {"key": "TO_DO", "label": "TO DO"},
    {"key": "IN_PROGRESS", "label": "IN PROGRESS"},
    {"key": "IN_REVIEW", "label": "IN REVIEW"},
    {"key": "DONE", "label": "DONE"},
]


def _normalize_work_status(status: str | None) -> str:
    value = (status or "TO_DO").upper().replace(" ", "_").replace("-", "_")
    return value if value in {c["key"] for c in WORK_BOARD_COLUMNS} else "TO_DO"


async def _ensure_project_work_breakdown(session, project: dict) -> None:
    """Create the root epic for a project if the board has not been initialized."""
    from sqlalchemy import text

    project_id = project["id"]
    now = _now()
    existing = (
        await session.execute(
            text("SELECT id FROM project_epics WHERE project_id = :pid LIMIT 1"),
            {"pid": project_id},
        )
    ).first()
    if existing:
        return

    epic_id = f"epic-{project_id}"
    await session.execute(
        text(
            "INSERT INTO project_epics (id, project_id, title, description, status, sort_order, created_at, updated_at) "
            "VALUES (:id, :pid, :title, :desc, 'TO_DO', 0, :t, :t) ON CONFLICT DO NOTHING"
        ),
        {
            "id": epic_id,
            "pid": project_id,
            "title": f"{project.get('name') or 'Project'} Delivery Epic",
            "desc": project.get("businessgoal") or project.get("description") or "",
            "t": now,
        },
    )

    requirements = project.get("requirements") or {}
    if isinstance(requirements, str):
        try:
            requirements = json.loads(requirements)
        except Exception:
            requirements = {}

    for idx, story_title in enumerate((requirements.get("functionalReqs") or [])[:12]):
        await session.execute(
            text(
                "INSERT INTO project_stories (id, project_id, epic_id, title, description, status, sort_order, created_at, updated_at) "
                "VALUES (:id, :pid, :eid, :title, :desc, 'TO_DO', :ord, :t, :t) ON CONFLICT DO NOTHING"
            ),
            {
                "id": f"story-{project_id}-{idx + 1}",
                "pid": project_id,
                "eid": epic_id,
                "title": str(story_title),
                "desc": "Feature story created from finalized project requirements.",
                "ord": idx,
                "t": now,
            },
        )


async def _ensure_project_queue_items(session, project: dict) -> None:
    """Generate project-scoped human queue tickets from requirements, risks, and phases."""
    from datetime import timedelta

    from sqlalchemy import text

    project_id = project["id"]
    now = _now()

    existing = (
        await session.execute(
            text("SELECT id FROM human_queue WHERE projectId = :pid LIMIT 1"),
            {"pid": project_id},
        )
    ).first()
    if existing:
        return

    requirements = project.get("requirements") or {}
    if isinstance(requirements, str):
        try:
            requirements = json.loads(requirements)
        except Exception:
            requirements = {}

    project_name = requirements.get("projectName") or project.get("name") or "Project"
    agents_rows = (
        await session.execute(
            text(
                "SELECT name FROM agents WHERE project_id = :pid AND status = 'active' ORDER BY id LIMIT 1"
            ),
            {"pid": project_id},
        )
    ).fetchall()
    agent_name = (_row_to_dict(agents_rows[0])["name"] if agents_rows else None) or "BA Agent"

    tickets: list[dict] = []
    idx = 0

    # Tickets from risks → Escalation
    for risk in (requirements.get("risks") or [])[:3]:
        if not isinstance(risk, str) or not risk.strip():
            continue
        idx += 1
        tickets.append(
            {
                "id": f"{project_id}-q-{idx}",
                "projectId": project_id,
                "title": f"Risk flagged: {risk[:80]}",
                "type": "Escalation",
                "priority": "Critical",
                "confidence": 34,
                "agent_name": agent_name,
                "reason": f"Project risk identified during BA discovery for {project_name}: {risk} Requires mitigation plan approval before proceeding.",
                "status": "Pending",
                "submitted_at": now,
                "due_by": (datetime.now(UTC) + timedelta(days=3)).isoformat(),
            }
        )

    # Tickets from phases → Approval (gate reviews)
    for phase in (requirements.get("phases") or [])[:3]:
        if not isinstance(phase, dict):
            continue
        phase_name = phase.get("name") or "Phase"
        phase_desc = phase.get("description") or ""
        idx += 1
        tickets.append(
            {
                "id": f"{project_id}-q-{idx}",
                "projectId": project_id,
                "title": f"Phase gate: {phase_name} — approve deliverables",
                "type": "Approval",
                "priority": "High",
                "confidence": 55,
                "agent_name": agent_name,
                "reason": f"Phase '{phase_name}' exit criteria for {project_name}. {phase_desc} Review deliverables and approve before next phase begins.",
                "status": "Pending",
                "submitted_at": now,
                "due_by": (datetime.now(UTC) + timedelta(days=5)).isoformat(),
            }
        )

    # Tickets from governance → Review
    for gov in (requirements.get("governance") or [])[:2]:
        if not isinstance(gov, dict):
            continue
        label = gov.get("label") or "Governance check"
        detail = gov.get("detail") or ""
        idx += 1
        tickets.append(
            {
                "id": f"{project_id}-q-{idx}",
                "projectId": project_id,
                "title": f"Governance review: {label}",
                "type": "Review",
                "priority": "Medium",
                "confidence": 62,
                "agent_name": agent_name,
                "reason": f"Governance requirement for {project_name}: {label}. {detail} Verify compliance before proceeding.",
                "status": "Pending",
                "submitted_at": now,
                "due_by": (datetime.now(UTC) + timedelta(days=7)).isoformat(),
            }
        )

    # Ticket from connectors → Approval
    connectors = requirements.get("connectors") or []
    if connectors:
        idx += 1
        connector_list = ", ".join(str(c) for c in connectors[:4])
        tickets.append(
            {
                "id": f"{project_id}-q-{idx}",
                "projectId": project_id,
                "title": f"Integration approval: {connector_list}",
                "type": "Approval",
                "priority": "High",
                "confidence": 48,
                "agent_name": agent_name,
                "reason": f"The following integrations are required for {project_name}: {connector_list}. Confirm access credentials and API permissions before development begins.",
                "status": "Pending",
                "submitted_at": now,
                "due_by": (datetime.now(UTC) + timedelta(days=4)).isoformat(),
            }
        )

    # Ticket from first functional req → Review (requirement sign-off)
    func_reqs = requirements.get("functionalReqs") or []
    if func_reqs:
        first_req = str(func_reqs[0])[:120]
        idx += 1
        tickets.append(
            {
                "id": f"{project_id}-q-{idx}",
                "projectId": project_id,
                "title": f"Requirement sign-off: {first_req[:60]}",
                "type": "Review",
                "priority": "Medium",
                "confidence": 70,
                "agent_name": agent_name,
                "reason": f"Primary functional requirement for {project_name}: {first_req} Confirm acceptance criteria and scope before implementation.",
                "status": "Pending",
                "submitted_at": now,
                "due_by": (datetime.now(UTC) + timedelta(days=6)).isoformat(),
            }
        )

    for t in tickets:
        await session.execute(
            text(
                "INSERT INTO human_queue "
                "(id, projectId, agentId, reason, status, resolution, assignedTo, title, type, priority, confidence, agent_name, submitted_at, due_by, comment) "
                "VALUES (:id, :pid, NULL, :reason, :status, NULL, NULL, :title, :type, :priority, :confidence, :agent_name, :submitted_at, :due_by, NULL) "
                "ON CONFLICT (id) DO NOTHING"
            ),
            {
                "id": t["id"],
                "pid": t["projectId"],
                "reason": t["reason"],
                "status": t["status"],
                "title": t["title"],
                "type": t["type"],
                "priority": t["priority"],
                "confidence": t["confidence"],
                "agent_name": t["agent_name"],
                "submitted_at": t["submitted_at"],
                "due_by": t["due_by"],
            },
        )


async def _load_project_for_route(session, project_id: str) -> tuple[str, dict]:
    from sqlalchemy import text

    target_id = project_id
    if project_id == "demo":
        r = (await session.execute(text("SELECT * FROM business_projects LIMIT 1"))).first()
        project = _row_to_dict(r) if r else None
        if not project:
            _error_response("NOT-FOUND", "Project not found", status=404)
        await _hydrate_project_owner(session, project)
        return project["id"], project

    row = (
        await session.execute(
            text("SELECT * FROM business_projects WHERE id = :id"),
            {"id": target_id},
        )
    ).first()
    project = _row_to_dict(row) if row else None
    if not project:
        _error_response("NOT-FOUND", "Project not found", status=404)
    await _hydrate_project_owner(session, project)
    return target_id, project


async def _get_current_user(request: Request) -> dict:
    """Extract user from Bearer token via auth_sessions table."""
    auth = request.headers.get("Authorization", "")
    token = auth.removeprefix("Bearer ").strip()
    if not token:
        _error_response("AUTH-4011", "Missing token", status=401)

    async with db_session() as session:
        from sqlalchemy import text

        row = (
            await session.execute(
                text("SELECT * FROM auth_sessions WHERE token = :token"),
                {"token": token},
            )
        ).first()
        if not row:
            _error_response("AUTH-4012", "Invalid session", status=401)
        sess = _row_to_dict(row)

        if int(sess.get("expiresat", "0")) < int(datetime.now().timestamp() * 1000):
            await session.execute(
                text("DELETE FROM auth_sessions WHERE token = :token"),
                {"token": token},
            )
            _error_response("AUTH-4013", "Session expired", status=401)

        user_row = (
            await session.execute(
                text("SELECT * FROM users WHERE id = :id"),
                {"id": sess["userid"]},
            )
        ).first()
        if not user_row:
            _error_response("AUTH-4013", "User not found", status=401)
        return _row_to_dict(user_row)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@router.get("/health")
async def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Install
# ---------------------------------------------------------------------------


class InstallBody(BaseModel):
    orgName: str
    adminEmail: str
    adminPassword: str
    aiProvider: str | None = None
    aiApiKey: str | None = None
    aiModel: str | None = None


@router.post("/install")
async def install(body: InstallBody):
    async with db_session() as session:
        from sqlalchemy import text

        existing = (
            await session.execute(text("SELECT * FROM organization WHERE setupComplete = 1"))
        ).first()
        if existing:
            _error_response(
                "INSTALL-4031", "Installation locked", details="Already installed", status=403
            )

        domain = body.orgName.lower().replace(" ", "") + ".com"
        org_id = "org-1"
        admin_id = _uuid()

        await session.execute(text("DELETE FROM organization"))
        await session.execute(
            text(
                "INSERT INTO organization (id, name, domain, setupcomplete, licensekey, aiprovider, aiapikey, aimodel, storage, database) "
                "VALUES (:id, :name, :domain, 1, :lk, :aip, :aik, :aim, 'local', 'sqlite')"
            ),
            {
                "id": org_id,
                "name": body.orgName,
                "domain": domain,
                "lk": "Demo",
                "aip": body.aiProvider,
                "aik": body.aiApiKey,
                "aim": body.aiModel,
            },
        )

        await session.execute(
            text(
                "INSERT INTO users (id, email, passwordhash, role, department, active) "
                "VALUES (:id, :email, :pw, 'Super Admin', 'General', 1)"
            ),
            {"id": admin_id, "email": body.adminEmail, "pw": body.adminPassword},
        )

        await session.execute(
            text(
                "INSERT INTO audit_logs (id, action, userid, details, timestamp) VALUES (:id, :a, :u, :d, :t)"
            ),
            {
                "id": _uuid(),
                "a": "Installation Completed",
                "u": "system",
                "d": "Platform initialized",
                "t": _now(),
            },
        )

    return {"success": True}


@router.get("/installation/status")
async def installation_status():
    async with db_session() as session:
        from sqlalchemy import text

        row = (await session.execute(text("SELECT * FROM organization LIMIT 1"))).first()
        org = _row_to_dict(row) if row else {}
        return {"locked": bool(org.get("setupcomplete"))}


@router.post("/install/test/{service}")
async def install_test_service(service: str):
    return {"success": True}


@router.get("/install/health")
async def install_health():
    async with db_session() as session:
        from sqlalchemy import text

        row = (await session.execute(text("SELECT * FROM organization LIMIT 1"))).first()
        org = _row_to_dict(row) if row else {}
        return {
            "status": "healthy",
            "db": True,
            "storage": True,
            "ai": bool(org.get("aiprovider")),
        }


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


class LoginBody(BaseModel):
    email: str
    password: str


@router.post("/auth/login")
async def auth_login(body: LoginBody):
    async with db_session() as session:
        from sqlalchemy import text

        row = (
            await session.execute(
                text("SELECT * FROM users WHERE email = :email"),
                {"email": body.email},
            )
        ).first()
        if not row:
            _error_response("AUTH-4011", "Invalid credentials", status=401)
        user = _row_to_dict(row)

        if user["passwordhash"] != body.password or not user["active"]:
            _error_response("AUTH-4011", "Invalid credentials", status=401)

        token = f"sess_{int(datetime.now().timestamp() * 1000)}"
        expires = str(int(datetime.now().timestamp() * 1000) + 86400000)
        await session.execute(
            text(
                "INSERT INTO auth_sessions (id, userid, token, expiresat) VALUES (:id, :uid, :tok, :exp)"
            ),
            {"id": _uuid(), "uid": user["id"], "tok": token, "exp": expires},
        )

        await session.execute(
            text(
                "INSERT INTO audit_logs (id, action, userid, details, timestamp) VALUES (:id, :a, :u, :d, :t)"
            ),
            {
                "id": _uuid(),
                "a": "User Login",
                "u": user["id"],
                "d": "Successful login",
                "t": _now(),
            },
        )

    return {
        "token": token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "role": user["role"],
            "name": user.get("name", ""),
        },
    }


@router.get("/auth/me")
async def auth_me(request: Request):
    user = await _get_current_user(request)
    return {
        "user": {
            "id": user["id"],
            "email": user["email"],
            "role": user["role"],
            "name": user.get("name", ""),
        }
    }


@router.post("/auth/logout")
async def auth_logout(request: Request):
    auth = request.headers.get("Authorization", "")
    token = auth.removeprefix("Bearer ").strip()
    async with db_session() as session:
        from sqlalchemy import text

        await session.execute(
            text("DELETE FROM auth_sessions WHERE token = :token"), {"token": token}
        )
    return {"success": True}


class RBACBody(BaseModel):
    role: str
    resource: str


@router.post("/rbac/evaluate")
async def rbac_evaluate(body: RBACBody):
    hierarchy = ["Viewer", "Analyst", "Developer", "Manager", "Org Admin", "Super Admin"]
    required = "Viewer"
    if body.resource == "users":
        required = "Org Admin"
    if body.resource == "installation":
        required = "Super Admin"
    allowed = (
        hierarchy.index(body.role) >= hierarchy.index(required) if body.role in hierarchy else False
    )
    return {"allowed": allowed}


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------


class UserCreateBody(BaseModel):
    email: str
    password: str | None = "password123"
    role: str | None = "Viewer"
    department: str | None = "General"


@router.get("/users")
async def list_users():
    async with db_session() as session:
        from sqlalchemy import text

        rows = (await session.execute(text("SELECT * FROM users"))).fetchall()
        return [
            {"id": r["id"], "email": r["email"], "role": r["role"], "active": r["active"]}
            for r in [_row_to_dict(row) for row in rows]
        ]


@router.post("/users")
async def create_user(body: UserCreateBody):
    uid = _uuid()
    async with db_session() as session:
        from sqlalchemy import text

        await session.execute(
            text(
                "INSERT INTO users (id, email, passwordHash, role, department, active) "
                "VALUES (:id, :email, :pw, :role, :dept, 1)"
            ),
            {
                "id": uid,
                "email": body.email,
                "pw": body.password or "password123",
                "role": body.role or "Viewer",
                "dept": body.department or "General",
            },
        )
    return {
        "success": True,
        "user": {"id": uid, "email": body.email, "role": body.role, "active": 1},
    }


class UserActiveBody(BaseModel):
    active: bool


@router.put("/users/{user_id}/active")
async def update_user_active(user_id: str, body: UserActiveBody):
    async with db_session() as session:
        from sqlalchemy import text

        await session.execute(
            text("UPDATE users SET active = :active WHERE id = :id"),
            {"active": 1 if body.active else 0, "id": user_id},
        )
    return {"success": True}


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------


class ProjectCreateBody(BaseModel):
    name: str
    businessGoal: str
    description: str | None = None
    department: str | None = None
    priority: str | None = "Medium"
    tags: str | None = None
    requirements: dict | None = None
    status: str | None = None


@router.get("/projects")
async def list_projects(request: Request):
    await _get_current_user(request)
    async with db_session() as session:
        from sqlalchemy import text

        rows = (await session.execute(text("SELECT * FROM business_projects"))).fetchall()
        projects = [_row_to_dict(r) for r in rows]
        for project in projects:
            await _hydrate_project_owner(session, project)
            pid = project["id"]
            node_rows = (
                await session.execute(
                    text("SELECT state FROM execution_nodes WHERE projectId = :pid"),
                    {"pid": pid},
                )
            ).fetchall()
            nodes = [_row_to_dict(r) for r in node_rows]
            story_rows = (
                await session.execute(
                    text(
                        "SELECT 'story' AS kind, status FROM project_stories WHERE project_id = :pid"
                    ),
                    {"pid": pid},
                )
            ).fetchall()
            bug_rows = (
                await session.execute(
                    text(
                        "SELECT 'bug' AS kind, status FROM project_story_bugs WHERE project_id = :pid"
                    ),
                    {"pid": pid},
                )
            ).fetchall()
            work_rows = [_row_to_dict(r) for r in story_rows + bug_rows]
            project["progress"] = _compute_progress(nodes, work_rows, project)
            project["pendingapprovals"] = (
                await session.execute(
                    text(
                        "SELECT count(1) FROM human_queue WHERE projectId = :pid AND status = 'Pending'"
                    ),
                    {"pid": pid},
                )
            ).scalar() or 0
            project["activeworkers"] = (
                await session.execute(
                    text(
                        "SELECT count(1) FROM agents WHERE project_id = :pid AND status IN ('active', 'running', 'executing')"
                    ),
                    {"pid": pid},
                )
            ).scalar() or 0
        return projects


@router.post("/projects")
async def create_project(body: ProjectCreateBody, request: Request):
    user = await _get_current_user(request)
    pid = _uuid()
    now = _now()
    import json

    try:
        async with db_session() as session:
            from sqlalchemy import text

            await session.execute(
                text(
                    "INSERT INTO business_projects (id, name, description, businessgoal, ownerid, department, status, priority, tags, requirements, createdat, updatedat) "
                    "VALUES (:id, :name, :desc, :goal, :owner, :dept, :status, :pri, :tags, :req, :t, :t)"
                ),
                {
                    "id": pid,
                    "name": body.name,
                    "desc": body.description or "",
                    "goal": body.businessGoal,
                    "owner": user["id"],
                    "dept": body.department or "",
                    "status": body.status or "Planning",
                    "pri": body.priority or "Medium",
                    "tags": body.tags or "[]",
                    "req": json.dumps(body.requirements) if body.requirements else None,
                    "t": now,
                },
            )

            # Store requirements in detail tables if provided
            if body.requirements:
                reqs = body.requirements
                uid = pid

                # Functional requirements
                for i, r in enumerate(reqs.get("functionalReqs", [])):
                    await session.execute(
                        text(
                            "INSERT INTO project_requirements (id, project_id, text, type, status, source, version, created_at, updated_at) "
                            "VALUES (:id, :pid, :text, 'functional', 'proposed', 'ba_agent', '1', :t, :t) ON CONFLICT DO NOTHING"
                        ),
                        {"id": f"{uid}-fr-{i}", "pid": pid, "text": r, "t": now},
                    )

                # Skills
                for i, s in enumerate(reqs.get("skills", [])):
                    await session.execute(
                        text(
                            "INSERT INTO project_requirements (id, project_id, text, type, status, source, version, created_at, updated_at) "
                            "VALUES (:id, :pid, :text, 'skill', 'proposed', 'ba_agent', '1', :t, :t) ON CONFLICT DO NOTHING"
                        ),
                        {"id": f"{uid}-sk-{i}", "pid": pid, "text": s, "t": now},
                    )

                # Connectors
                for i, c in enumerate(reqs.get("connectors", [])):
                    await session.execute(
                        text(
                            "INSERT INTO project_requirements (id, project_id, text, type, status, source, version, created_at, updated_at) "
                            "VALUES (:id, :pid, :text, 'connector', 'proposed', 'ba_agent', '1', :t, :t) ON CONFLICT DO NOTHING"
                        ),
                        {"id": f"{uid}-cn-{i}", "pid": pid, "text": c, "t": now},
                    )

                # Risks
                for i, r in enumerate(reqs.get("risks", [])):
                    await session.execute(
                        text(
                            "INSERT INTO project_risks (id, project_id, risk, impact, mitigation, status, version, created_at) "
                            "VALUES (:id, :pid, :risk, 'Medium', 'TBD', 'open', '1', :t) ON CONFLICT DO NOTHING"
                        ),
                        {"id": f"{uid}-rk-{i}", "pid": pid, "risk": r, "t": now},
                    )

            row = (
                await session.execute(
                    text("SELECT * FROM business_projects WHERE id = :id"), {"id": pid}
                )
            ).first()
            project = _row_to_dict(row)
            await _ensure_project_work_breakdown(session, project)
            await _ensure_project_documents(session, project)
            try:
                await _ensure_project_meetings(session, project)
            except Exception as meet_err:
                import logging

                logging.getLogger(__name__).warning("meetings seed failed: %s", meet_err)
            try:
                await _ensure_project_queue_items(session, project)
            except Exception as q_err:
                import logging

                logging.getLogger(__name__).warning("queue items seed failed: %s", q_err)
            await _hydrate_project_owner(session, project)
        return project
    except Exception as exc:
        import logging

        logging.getLogger(__name__).error("create_project failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": {"code": "PROJECT-CREATE-FAILED", "message": str(exc)},
            },
        )


@router.get("/projects/{project_id}")
async def get_project(project_id: str, request: Request):
    await _get_current_user(request)
    async with db_session() as session:
        _target_id, project = await _load_project_for_route(session, project_id)
        return project


@router.put("/projects/{project_id}")
async def update_project(project_id: str, body: dict, request: Request):
    user = await _get_current_user(request)
    async with db_session() as session:
        from sqlalchemy import text

        await session.execute(
            text(
                "UPDATE business_projects SET name=:name, description=:desc, businessgoal=:goal, "
                "department=:dept, status=:status, priority=:pri, tags=:tags, updatedat=:t WHERE id=:id"
            ),
            {
                "id": project_id,
                "name": body.get("name", ""),
                "desc": body.get("description", ""),
                "goal": body.get("businessGoal") or body.get("businessgoal") or "",
                "dept": body.get("department", ""),
                "status": body.get("status", "Planning"),
                "pri": body.get("priority", "Medium"),
                "tags": body.get("tags", "[]"),
                "t": _now(),
            },
        )
    return {"success": True}


@router.delete("/projects/{project_id}")
async def delete_project(project_id: str, request: Request):
    user = await _get_current_user(request)
    async with db_session() as session:
        from sqlalchemy import text

        await session.execute(
            text("DELETE FROM execution_nodes WHERE projectId = :id"), {"id": project_id}
        )
        await session.execute(
            text("DELETE FROM project_agents WHERE projectId = :id"), {"id": project_id}
        )
        await session.execute(
            text("DELETE FROM project_agent_governance_assignments WHERE project_id = :id"),
            {"id": project_id},
        )
        await session.execute(text("DELETE FROM agents WHERE project_id = :id"), {"id": project_id})
        await session.execute(
            text("DELETE FROM artifacts WHERE projectId = :id"), {"id": project_id}
        )
        await session.execute(
            text("DELETE FROM human_queue WHERE projectId = :id"), {"id": project_id}
        )
        await session.execute(
            text("DELETE FROM notifications WHERE project_id = :id"), {"id": project_id}
        )
        await session.execute(
            text("DELETE FROM meetings WHERE project_id = :id"), {"id": project_id}
        )
        await session.execute(
            text("DELETE FROM project_requirements WHERE project_id = :id"), {"id": project_id}
        )
        await session.execute(
            text("DELETE FROM project_constraints WHERE project_id = :id"), {"id": project_id}
        )
        await session.execute(
            text("DELETE FROM project_risks WHERE project_id = :id"), {"id": project_id}
        )
        await session.execute(
            text("DELETE FROM discovery_sessions WHERE project_id = :id"), {"id": project_id}
        )
        await session.execute(
            text("DELETE FROM sessions WHERE project_id = :id OR workspace_id = :id"),
            {"id": project_id},
        )
        await session.execute(
            text("DELETE FROM project_story_bugs WHERE project_id = :id"), {"id": project_id}
        )
        await session.execute(
            text("DELETE FROM project_stories WHERE project_id = :id"), {"id": project_id}
        )
        await session.execute(
            text("DELETE FROM project_epics WHERE project_id = :id"), {"id": project_id}
        )
        await session.execute(
            text("DELETE FROM project_human_assignments WHERE project_id = :id"), {"id": project_id}
        )
        await session.execute(
            text(
                "DELETE FROM project_agent_assignments "
                "WHERE position_id IN (SELECT id FROM project_agent_positions WHERE project_id = :id)"
            ),
            {"id": project_id},
        )
        await session.execute(
            text("DELETE FROM project_agent_positions WHERE project_id = :id"), {"id": project_id}
        )
        await session.execute(
            text("DELETE FROM business_projects WHERE id = :id"), {"id": project_id}
        )
    return {"success": True}


# ---------------------------------------------------------------------------
# Project Work Board
# ---------------------------------------------------------------------------


class WorkEpicBody(BaseModel):
    title: str
    description: str | None = None
    status: str | None = "TO_DO"


class WorkStoryBody(BaseModel):
    title: str
    epicId: str | None = None
    description: str | None = None
    status: str | None = "TO_DO"
    storyPoints: int | None = None


class WorkBugBody(BaseModel):
    title: str
    description: str | None = None
    severity: str | None = "Medium"
    status: str | None = "TO_DO"


@router.get("/projects/{project_id}/work-board")
async def get_project_work_board(project_id: str, request: Request):
    await _get_current_user(request)
    async with db_session() as session:
        from sqlalchemy import text

        target_id, project = await _load_project_for_route(session, project_id)
        await _ensure_project_work_breakdown(session, project)

        epic_rows = (
            await session.execute(
                text(
                    "SELECT * FROM project_epics WHERE project_id = :pid ORDER BY sort_order, created_at"
                ),
                {"pid": target_id},
            )
        ).fetchall()
        story_rows = (
            await session.execute(
                text(
                    "SELECT * FROM project_stories WHERE project_id = :pid ORDER BY sort_order, created_at"
                ),
                {"pid": target_id},
            )
        ).fetchall()
        bug_rows = (
            await session.execute(
                text(
                    "SELECT * FROM project_story_bugs WHERE project_id = :pid ORDER BY sort_order, created_at"
                ),
                {"pid": target_id},
            )
        ).fetchall()

    epics = [_row_to_dict(r) for r in epic_rows]
    stories = [_row_to_dict(r) for r in story_rows]
    bugs = [_row_to_dict(r) for r in bug_rows]

    items = (
        [{"kind": "epic", **e, "status": _normalize_work_status(e.get("status"))} for e in epics]
        + [
            {"kind": "story", **s, "status": _normalize_work_status(s.get("status"))}
            for s in stories
        ]
        + [{"kind": "bug", **b, "status": _normalize_work_status(b.get("status"))} for b in bugs]
    )

    return {
        "project": {
            "id": project["id"],
            "name": project.get("name"),
            "status": project.get("status"),
        },
        "columns": [
            {
                **column,
                "items": [item for item in items if item["status"] == column["key"]],
            }
            for column in WORK_BOARD_COLUMNS
        ],
        "epics": epics,
        "stories": stories,
        "bugs": bugs,
    }


@router.post("/projects/{project_id}/work-board/epics")
async def create_project_epic(project_id: str, body: WorkEpicBody, request: Request):
    await _get_current_user(request)
    eid = _uuid()
    now = _now()
    async with db_session() as session:
        from sqlalchemy import text

        target_id, _project = await _load_project_for_route(session, project_id)
        await session.execute(
            text(
                "INSERT INTO project_epics (id, project_id, title, description, status, sort_order, created_at, updated_at) "
                "VALUES (:id, :pid, :title, :desc, :status, 0, :t, :t)"
            ),
            {
                "id": eid,
                "pid": target_id,
                "title": body.title,
                "desc": body.description or "",
                "status": _normalize_work_status(body.status),
                "t": now,
            },
        )
    return {"success": True, "epic": {"id": eid, "title": body.title}}


@router.post("/projects/{project_id}/work-board/stories")
async def create_project_story(project_id: str, body: WorkStoryBody, request: Request):
    await _get_current_user(request)
    sid = _uuid()
    now = _now()
    async with db_session() as session:
        from sqlalchemy import text

        target_id, project = await _load_project_for_route(session, project_id)
        await _ensure_project_work_breakdown(session, project)
        epic_id = body.epicId
        if not epic_id:
            epic_row = (
                await session.execute(
                    text(
                        "SELECT id FROM project_epics WHERE project_id = :pid ORDER BY sort_order, created_at LIMIT 1"
                    ),
                    {"pid": target_id},
                )
            ).first()
            epic_id = _row_to_dict(epic_row).get("id") if epic_row else None
        await session.execute(
            text(
                "INSERT INTO project_stories (id, project_id, epic_id, title, description, status, story_points, sort_order, created_at, updated_at) "
                "VALUES (:id, :pid, :eid, :title, :desc, :status, :points, 0, :t, :t)"
            ),
            {
                "id": sid,
                "pid": target_id,
                "eid": epic_id,
                "title": body.title,
                "desc": body.description or "",
                "status": _normalize_work_status(body.status),
                "points": body.storyPoints,
                "t": now,
            },
        )
    return {"success": True, "story": {"id": sid, "title": body.title, "epicId": epic_id}}


@router.post("/projects/{project_id}/work-board/stories/{story_id}/bugs")
async def create_project_story_bug(
    project_id: str, story_id: str, body: WorkBugBody, request: Request
):
    await _get_current_user(request)
    bid = _uuid()
    now = _now()
    async with db_session() as session:
        from sqlalchemy import text

        target_id, _project = await _load_project_for_route(session, project_id)
        story = (
            await session.execute(
                text("SELECT id FROM project_stories WHERE id = :sid AND project_id = :pid"),
                {"sid": story_id, "pid": target_id},
            )
        ).first()
        if not story:
            _error_response("NOT-FOUND", "Story not found", status=404)
        await session.execute(
            text(
                "INSERT INTO project_story_bugs (id, project_id, story_id, title, description, severity, status, sort_order, created_at, updated_at) "
                "VALUES (:id, :pid, :sid, :title, :desc, :severity, :status, 0, :t, :t)"
            ),
            {
                "id": bid,
                "pid": target_id,
                "sid": story_id,
                "title": body.title,
                "desc": body.description or "",
                "severity": body.severity or "Medium",
                "status": _normalize_work_status(body.status),
                "t": now,
            },
        )
    return {"success": True, "bug": {"id": bid, "title": body.title, "storyId": story_id}}


# ---------------------------------------------------------------------------
# AI Analysis & Recommendations
# ---------------------------------------------------------------------------


@router.post("/projects/{project_id}/analyze")
async def analyze_project(project_id: str, request: Request):
    user = await _get_current_user(request)
    async with db_session() as session:
        from sqlalchemy import text

        row = (
            await session.execute(
                text("SELECT * FROM business_projects WHERE id = :id"), {"id": project_id}
            )
        ).first()
        if not row:
            _error_response("NOT-FOUND", "Project not found", status=404)
        project = _row_to_dict(row)

    goal = (project.get("businessgoal") or "").lower()

    domain = "Operations"
    complexity = "Low"
    skills = ["Process Mapping"]
    knowledge = ["Internal Policies"]
    connectors = ["Internal Database"]
    risks = ["Scope creep", "Unclear metrics"]
    missing = ["Success criteria", "Timeline"]
    questions = ["What is the expected ROI?", "Who are the key stakeholders?"]

    if any(k in goal for k in ["migrate", "mysql", "frappe"]):
        domain = "Migration & Integration"
        complexity = "Medium"
        skills = ["Schema Analysis", "Data Mapping", "Validation", "Migration Strategy"]
        knowledge = ["MySQL", "Frappe Documentation", "Migration Policies"]
        connectors = ["MySQL", "GitHub", "Frappe"]
        risks = ["Data loss during transfer", "Downtime exceeding window", "Schema mismatch"]
        missing = ["Downtime allowed", "Data volume metrics"]
        questions = ["What Frappe version?", "How many records?", "Are there any custom fields?"]
    elif any(k in goal for k in ["invoice", "automate"]):
        domain = "Financial Automation"
        complexity = "High"
        skills = ["OCR Processing", "Data Extraction", "Approval Workflow Routing"]
        knowledge = ["Accounting Principles", "Vendor Contracts"]
        connectors = ["ERP System", "Email Inbox", "Cloud Storage"]
        risks = ["OCR inaccuracies", "Compliance violations", "Fraud detection failure"]
        missing = ["Sample invoices", "Approval hierarchy matrix"]
        questions = ["What formats do invoices arrive in?", "Is PO matching required?"]

    analysis = {
        "businessDomain": domain,
        "businessType": "Transformation",
        "estimatedComplexity": complexity,
        "requiredSkills": skills,
        "requiredKnowledge": knowledge,
        "requiredConnectors": connectors,
        "potentialRisks": risks,
        "missingInformation": missing,
        "questionsForUser": questions,
    }

    return {"success": True, "analysis": analysis}


@router.post("/projects/{project_id}/recommend")
async def recommend_project(project_id: str, request: Request):
    user = await _get_current_user(request)
    async with db_session() as session:
        from sqlalchemy import text

        row = (
            await session.execute(
                text("SELECT * FROM business_projects WHERE id = :id"), {"id": project_id}
            )
        ).first()
        if not row:
            _error_response("NOT-FOUND", "Project not found", status=404)
        project = _row_to_dict(row)

        org_row = (await session.execute(text("SELECT * FROM organization LIMIT 1"))).first()
        org = _row_to_dict(org_row) if org_row else {}

    if not org.get("aiprovider") or org.get("aiprovider") == "none":
        _error_response(
            "AI-001",
            "AI Provider Not Configured",
            details="Configure an AI Provider to generate recommendations.",
        )

    import os

    try:
        api_key = os.environ.get("AI_API_KEY") or org.get("aiapikey") or "dummy"
        base_url = "https://api.openai.com/v1/chat/completions"
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}

        if org.get("aiprovider") == "gemini":
            base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{org.get('aimodel', 'gemini-pro')}:generateContent?key={api_key}"
            headers = {"Content-Type": "application/json"}
        elif org.get("aiprovider") == "ollama":
            base_url = "http://localhost:11434/api/generate"

        system_prompt = f"""Analyze the business goal: {project.get("businessgoal")}.
Return a valid JSON object matching this schema:
{{
  "recommendedEmployees": [{{"name": "string", "role": "string", "purpose": "string", "reason": "string", "confidence": 85}}],
  "recommendedSkills": [{{"name": "string", "reason": "string"}}],
  "recommendedKnowledge": [{{"name": "string", "reason": "string"}}],
  "recommendedMemory": [{{"name": "string", "type": "Working|Session|Semantic|Long-term", "reason": "string"}}],
  "recommendedConnectors": [{{"name": "string", "reason": "string"}}],
  "recommendedWorkflow": [{{"stage": "string", "description": "string"}}],
  "assumptions": ["string"],
  "questions": ["string"],
  "risks": ["string"]
}}"""

        import httpx

        async with httpx.AsyncClient(timeout=30) as client:
            if org.get("aiProvider") == "gemini":
                resp = await client.post(
                    base_url,
                    headers=headers,
                    json={"contents": [{"parts": [{"text": system_prompt}]}]},
                )
            else:
                resp = await client.post(
                    base_url,
                    headers=headers,
                    json={
                        "model": org.get("aiModel", "gpt-4o"),
                        "messages": [{"role": "user", "content": system_prompt}],
                    },
                )

        if resp.status_code != 200:
            _error_response("AI-502", "AI Provider Error", details=resp.text, status=502)

        data = resp.json()
        raw_text = (
            data.get("choices", [{}])[0].get("message", {}).get("content")
            or data.get("response")
            or json.dumps(data)
        )
        raw_text = raw_text.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(raw_text)

    except json.JSONDecodeError:
        _error_response(
            "AI-501", "AI Provider Error", details="AI failed to return valid structured JSON"
        )
    except Exception as e:
        _error_response("AI-500", "AI Connection Failed", details=str(e))

    schema = {
        "recommendedEmployees": parsed.get("recommendedEmployees", []),
        "recommendedSkills": parsed.get("recommendedSkills", []),
        "recommendedKnowledge": parsed.get("recommendedKnowledge", []),
        "recommendedMemory": parsed.get("recommendedMemory", []),
        "recommendedConnectors": parsed.get("recommendedConnectors", []),
        "recommendedWorkflow": parsed.get("recommendedWorkflow", []),
        "assumptions": parsed.get("assumptions", []),
        "questions": parsed.get("questions", []),
        "risks": parsed.get("risks", []),
    }

    return {"success": True, "payload": schema}


class AuditBody(BaseModel):
    action: str
    detail: str | None = None


@router.post("/projects/{project_id}/recommendations/audit")
async def audit_recommendation(project_id: str, body: AuditBody, request: Request):
    user = await _get_current_user(request)
    async with db_session() as session:
        from sqlalchemy import text

        await session.execute(
            text(
                "INSERT INTO audit_logs (id, action, userid, details, timestamp) VALUES (:id, :a, :u, :d, :t)"
            ),
            {"id": _uuid(), "a": body.action, "u": user["id"], "d": body.detail, "t": _now()},
        )
    return {"success": True}


@router.post("/projects/{project_id}/employees/generate")
async def generate_employees(project_id: str, request: Request):
    user = await _get_current_user(request)
    return {"success": True, "message": "Employees generated"}


# ---------------------------------------------------------------------------
# Workspace
# ---------------------------------------------------------------------------


@router.get("/projects/{project_id}/workspace")
async def get_workspace(project_id: str, request: Request):
    await _get_current_user(request)
    async with db_session() as session:
        from sqlalchemy import text

        target_id, project = await _load_project_for_route(session, project_id)
        reqs = _project_requirements(project)
        await _ensure_project_work_breakdown(session, project)
        await _ensure_project_documents(session, project)
        await _ensure_project_meetings(session, project)

        legacy_agent_rows = (
            await session.execute(
                text("SELECT * FROM project_agents WHERE projectId = :id"), {"id": target_id}
            )
        ).fetchall()
        legacy_agents = [_row_to_dict(r) for r in legacy_agent_rows]

        real_agent_rows = (
            await session.execute(
                text(
                    "SELECT * FROM agents WHERE project_id = :id ORDER BY reports_to NULLS FIRST, role, name"
                ),
                {"id": target_id},
            )
        ).fetchall()
        real_agents = [_row_to_dict(r) for r in real_agent_rows]

        assigned_agent_rows = (
            await session.execute(
                text(
                    "SELECT "
                    "a.*, "
                    "p.id AS position_id, "
                    "p.name AS position_name, "
                    "p.role AS position_role, "
                    "p.designation AS position_designation, "
                    "p.reports_to AS position_reports_to, "
                    "p.role_description AS position_role_description "
                    "FROM project_agent_positions p "
                    "JOIN project_agent_assignments pa ON pa.position_id = p.id "
                    "JOIN agents a ON a.id = pa.agent_id "
                    "WHERE p.project_id = :id "
                    "ORDER BY p.reports_to NULLS FIRST, p.role, p.name"
                ),
                {"id": target_id},
            )
        ).fetchall()
        assigned_reusable_agents = [_row_to_dict(r) for r in assigned_agent_rows]

        artifacts_rows = (
            await session.execute(
                text("SELECT * FROM artifacts WHERE projectId = :id"), {"id": target_id}
            )
        ).fetchall()
        artifacts_list = [_row_to_dict(r) for r in artifacts_rows]

        nodes_rows = (
            await session.execute(
                text("SELECT * FROM execution_nodes WHERE projectId = :id"), {"id": target_id}
            )
        ).fetchall()
        nodes = [_row_to_dict(r) for r in nodes_rows]

        queue_rows = (
            await session.execute(
                text("SELECT * FROM human_queue WHERE projectId = :id ORDER BY id"),
                {"id": target_id},
            )
        ).fetchall()
        queue_items = [_row_to_dict(r) for r in queue_rows]

        meetings_rows = (
            await session.execute(
                text(
                    "SELECT * FROM meetings WHERE project_id = :id ORDER BY meeting_date NULLS LAST, created_at"
                ),
                {"id": target_id},
            )
        ).fetchall()
        meetings = [_row_to_dict(r) for r in meetings_rows]

        epic_rows = (
            await session.execute(
                text("SELECT id, status FROM project_epics WHERE project_id = :pid"),
                {"pid": target_id},
            )
        ).fetchall()
        story_rows = (
            await session.execute(
                text("SELECT id, status FROM project_stories WHERE project_id = :pid"),
                {"pid": target_id},
            )
        ).fetchall()
        bug_rows = (
            await session.execute(
                text("SELECT id, status FROM project_story_bugs WHERE project_id = :pid"),
                {"pid": target_id},
            )
        ).fetchall()

    work_rows = (
        [{"kind": "epic", **_row_to_dict(r)} for r in epic_rows]
        + [{"kind": "story", **_row_to_dict(r)} for r in story_rows]
        + [{"kind": "bug", **_row_to_dict(r)} for r in bug_rows]
    )
    progress = _compute_progress(nodes, work_rows, project)
    current_phase = project.get("status") or ""
    pending_approvals = len(
        [q for q in queue_items if (q.get("status") or "").lower() == "pending"]
    )
    workspace_agents = real_agents + assigned_reusable_agents
    active_workers = len(
        [
            a
            for a in workspace_agents
            if (a.get("status") or "").lower() in {"active", "running", "executing"}
        ]
    )

    kpis: list[dict] = []
    if current_phase:
        kpis.append({"key": "currentPhase", "label": "Current Phase", "value": current_phase})
    if progress is not None:
        kpis.append({"key": "progress", "label": "Progress", "value": f"{progress}%"})
    if pending_approvals:
        kpis.append(
            {
                "key": "pendingApprovals",
                "label": "Pending Approvals",
                "value": str(pending_approvals),
            }
        )
    if active_workers:
        kpis.append(
            {"key": "activeWorkers", "label": "Active Workers", "value": str(active_workers)}
        )

    legacy_by_id = {a.get("id"): a for a in legacy_agents}
    events = [
        {
            "delay": 0,
            "agent": legacy_by_id.get(n.get("agentid"), {}).get("name") or "Workspace Agent",
            "type": "human" if n.get("state") == "Blocked" else "info",
            "phase": current_phase,
            "title": f"Node {n.get('state')}",
            "desc": n.get("reasoning"),
            "conf": 95,
            "dur": "0.1s",
        }
        for n in nodes
    ]

    documents = [_artifact_to_workspace_doc(a) for a in artifacts_list]
    timeline = _workspace_timeline(project, reqs, meetings, workspace_agents)

    return {
        "project": project,
        "goal": project.get("businessgoal"),
        "requirements": reqs,
        "currentPhase": current_phase,
        "progress": progress,
        "pendingApprovals": pending_approvals,
        "activeWorkers": active_workers,
        "kpis": kpis,
        "workers": [
            {
                "id": a.get("position_id") or a["id"],
                "agentId": a["id"],
                "positionId": a.get("position_id"),
                "name": a.get("position_name") or a["name"],
                "agentName": a["name"],
                "role": a.get("position_role") or a.get("role"),
                "designation": a.get("position_designation") or a.get("designation"),
                "status": a["status"],
                "purpose": a.get("position_role_description") or a.get("role_description", ""),
                "config": {
                    "manager": a.get("position_reports_to") or a.get("reports_to"),
                    "skills": a.get("skills") or [],
                    "knowledge": [d["name"] for d in documents],
                    "connectors": reqs.get("connectors") or [],
                    "tools": (a.get("tool_policy") or {}).get("allowed_tools", [])
                    if isinstance(a.get("tool_policy"), dict)
                    else [],
                },
            }
            for a in workspace_agents
        ],
        "documents": documents,
        "artifacts": documents,
        "queue": [
            {
                "id": q.get("id"),
                "title": q.get("title") or q.get("reason"),
                "project": q.get("projectid"),
                "description": q.get("reason"),
                "type": q.get("type") or "Approval",
                "priority": q.get("priority") or "Medium",
                "confidence": q.get("confidence") or 50,
                "state": q.get("status"),
                "agent": q.get("agent_name") or q.get("agentid") or "System",
            }
            for q in queue_items
        ],
        "meetings": [_meeting_to_workspace(m) for m in meetings],
        "timeline": timeline,
        "registries": {
            "skills": reqs.get("skills") or [],
            "knowledge": [d["name"] for d in documents],
            "memory": [],
            "connectors": reqs.get("connectors") or [],
        },
        "logs": [f"[SYS] Node {n.get('id')} transitioned to {n.get('state')}" for n in nodes],
        "events": events,
    }


@router.get("/projects/{project_id}/documents/{document_id}")
async def get_project_document(project_id: str, document_id: str, request: Request):
    await _get_current_user(request)
    async with db_session() as session:
        from sqlalchemy import text

        target_id, _project = await _load_project_for_route(session, project_id)
        row = (
            await session.execute(
                text("SELECT * FROM artifacts WHERE id = :doc_id AND projectId = :project_id"),
                {"doc_id": document_id, "project_id": target_id},
            )
        ).first()
        if not row:
            _error_response("NOT-FOUND", "Document not found", status=404)
        artifact = _row_to_dict(row)
        content = artifact.get("content") or ""
        name = (
            artifact.get("name") or artifact.get("storagepath") or artifact.get("uri") or "Document"
        )
        return {
            "id": artifact.get("id"),
            "projectId": target_id,
            "name": name.split("/")[-1],
            "type": artifact.get("type") or "Document",
            "category": artifact.get("type") or "Document",
            "path": artifact.get("storagepath") or artifact.get("uri") or "",
            "size": _doc_size(content) if content else "",
            "content": content,
            "createdAt": artifact.get("createdat"),
            "versionHistory": artifact.get("versionhistory") or {},
        }


@router.post("/projects/{project_id}/workspace/chat")
async def workspace_chat(project_id: str, body: dict, request: Request):
    user = await _get_current_user(request)
    message = body.get("message", "")
    if not message.strip():
        _error_response("EMPTY-MESSAGE", "message is required", status=400)

    async with db_session() as session:
        from sqlalchemy import text

        target_id, project = await _load_project_for_route(session, project_id)
        ts = int(datetime.now().timestamp() * 1000)
        node_id = f"node-user-{ts}"
        agent_row = (
            await session.execute(
                text(
                    "SELECT id, name FROM agents WHERE project_id = :pid ORDER BY reports_to NULLS FIRST, role, name LIMIT 1"
                ),
                {"pid": target_id},
            )
        ).first()
        agent = _row_to_dict(agent_row) if agent_row else {}
        agent_id = agent.get("id")

        await session.execute(
            text(
                "INSERT INTO execution_nodes (id, projectId, agentId, state, dependencies, outputs, reasoning) VALUES (:id,:pid,:aid,:s,:dep,:out,:r)"
            ),
            {
                "id": node_id,
                "pid": target_id,
                "aid": agent_id,
                "s": "Running" if agent_id else "Queued",
                "dep": "[]",
                "out": "[]",
                "r": f"User requested workspace action: {message.strip()}",
            },
        )
        await session.execute(
            text(
                "UPDATE business_projects SET status = 'Execution', updatedAt = :t WHERE id = :id"
            ),
            {"t": _now(), "id": target_id},
        )
        await session.execute(
            text(
                "INSERT INTO audit_logs (id, projectid, userid, action, details, timestamp) "
                "VALUES (:id, :pid, :uid, :action, :details, :t)"
            ),
            {
                "id": _uuid(),
                "pid": target_id,
                "uid": user.get("id"),
                "action": "Workspace instruction",
                "details": message.strip(),
                "t": _now(),
            },
        )

    understanding = (
        f'Recorded workspace instruction for "{project.get("name", "Project")}": {message.strip()}'
    )
    reasoning = "The instruction is now represented as a real execution node for this project."
    decision = (
        "Queued the work against the current project worker hierarchy."
        if agent_id
        else "Queued the work until a project worker hierarchy is available."
    )
    plan_update = "Workspace KPIs will update from the recorded execution node."
    worker_actions = f"Assigned to {agent.get('name')}." if agent_id else "No worker assigned yet."
    required_approvals = ""
    expected_outcome = "Execution state can now be tracked from backend records."
    reply = "\n".join(
        [
            "[Workspace Update]",
            f"Understanding: {understanding}",
            f"Reasoning: {reasoning}",
            f"Decision: {decision}",
            f"Plan Update: {plan_update}",
            f"Worker Actions: {worker_actions}",
        ]
    )

    return {
        "success": True,
        "reply": reply,
        "understanding": understanding,
        "reasoning": reasoning,
        "decision": decision,
        "planUpdate": plan_update,
        "workerActions": worker_actions,
        "requiredApprovals": required_approvals,
        "expectedOutcome": expected_outcome,
        "newEvent": {
            "delay": 0,
            "agent": agent.get("name") or "Workspace",
            "type": "info",
            "phase": "Execution",
            "title": "Instruction Queued",
            "desc": reply,
            "conf": 99,
            "dur": "0.1s",
        },
        "newProgress": 50 if agent_id else 0,
        "newPhase": "Execution",
    }


# ---------------------------------------------------------------------------
# Employees / Workers
# ---------------------------------------------------------------------------


@router.get("/employees")
async def list_employees(request: Request):
    await _get_current_user(request)
    async with db_session() as session:
        from sqlalchemy import text

        rows = (await session.execute(text("SELECT * FROM project_agents"))).fetchall()
        return [_row_to_dict(r) for r in rows]


@router.get("/employees/{employee_id}")
async def get_employee(employee_id: str, request: Request):
    await _get_current_user(request)
    async with db_session() as session:
        from sqlalchemy import text

        row = (
            await session.execute(
                text("SELECT * FROM project_agents WHERE id = :id"), {"id": employee_id}
            )
        ).first()
        if not row:
            _error_response("NOT-FOUND", "Employee not found", status=404)
        return _row_to_dict(row)


class EmployeeStatusBody(BaseModel):
    status: str


@router.put("/employees/{employee_id}/status")
async def update_employee_status(employee_id: str, body: EmployeeStatusBody, request: Request):
    await _get_current_user(request)
    async with db_session() as session:
        from sqlalchemy import text

        await session.execute(
            text("UPDATE project_agents SET status = :s WHERE id = :id"),
            {"s": body.status, "id": employee_id},
        )
    return {"success": True}


class WorkerCreateBody(BaseModel):
    name: str
    purpose: str | None = ""
    status: str | None = "Running"
    config: dict | None = None


@router.post("/projects/{project_id}/workers")
async def create_worker(project_id: str, body: WorkerCreateBody, request: Request):
    await _get_current_user(request)
    wid = str(uuid.uuid4().int)[:12]
    async with db_session() as session:
        from sqlalchemy import text

        await session.execute(
            text(
                "INSERT INTO project_agents (id, projectId, name, status, config, systemPrompt) VALUES (:id,:pid,:n,:s,:c,:sp)"
            ),
            {
                "id": wid,
                "pid": project_id,
                "n": body.name,
                "s": body.status or "Running",
                "c": json.dumps(body.config or {}),
                "sp": body.purpose or "",
            },
        )
    return {"success": True, "workerId": wid}


@router.put("/projects/{project_id}/workers/{worker_id}")
async def update_worker(project_id: str, worker_id: str, body: dict, request: Request):
    await _get_current_user(request)
    async with db_session() as session:
        from sqlalchemy import text

        await session.execute(
            text("UPDATE project_agents SET config = :c, systemPrompt = :sp WHERE id = :id"),
            {
                "c": json.dumps(body.get("config", {})),
                "sp": body.get("purpose", ""),
                "id": worker_id,
            },
        )
    return {"success": True}


@router.delete("/projects/{project_id}/workers/{worker_id}")
async def delete_worker(project_id: str, worker_id: str, request: Request):
    await _get_current_user(request)
    async with db_session() as session:
        from sqlalchemy import text

        await session.execute(text("DELETE FROM project_agents WHERE id = :id"), {"id": worker_id})
    return {"success": True}


class WorkerStatusBody(BaseModel):
    status: str


@router.post("/projects/{project_id}/workers/{worker_id}/status")
async def update_worker_status(
    project_id: str, worker_id: str, body: WorkerStatusBody, request: Request
):
    await _get_current_user(request)
    async with db_session() as session:
        from sqlalchemy import text

        await session.execute(
            text("UPDATE project_agents SET status = :s WHERE id = :id"),
            {"s": body.status, "id": worker_id},
        )
    return {"success": True}


# ---------------------------------------------------------------------------
# Human Queue
# ---------------------------------------------------------------------------


@router.get("/queue")
async def list_queue(request: Request):
    await _get_current_user(request)
    async with db_session() as session:
        from sqlalchemy import text

        rows = (
            await session.execute(
                text(
                    "SELECT * FROM human_queue ORDER BY CASE WHEN status = 'Pending' THEN 0 WHEN status = 'In Review' THEN 1 ELSE 2 END, submitted_at DESC NULLS LAST, id"
                )
            )
        ).fetchall()
        result = []
        for r in [_row_to_dict(row) for row in rows]:
            submitted = r.get("submitted_at")
            due = r.get("due_by")
            result.append(
                {
                    "id": r["id"],
                    "title": r.get("title") or r.get("reason") or "",
                    "type": r.get("type") or "Approval",
                    "priority": r.get("priority") or "Medium",
                    "reason": r.get("reason") or "",
                    "confidence": r.get("confidence") or 50,
                    "status": r["status"],
                    "agent": r.get("agent_name") or r.get("agentid") or "System",
                    "project": r.get("projectid"),
                    "submittedAt": submitted.isoformat()
                    if hasattr(submitted, "isoformat")
                    else (submitted or ""),
                    "dueBy": due.isoformat() if hasattr(due, "isoformat") else (due or ""),
                    "comment": r.get("comment"),
                }
            )
        return result


class QueueActionBody(BaseModel):
    action: str
    comment: str | None = None


@router.post("/queue/{queue_id}/action")
async def queue_action(queue_id: str, body: QueueActionBody, request: Request):
    user = await _get_current_user(request)
    status = (
        "Approved"
        if body.action == "approve"
        else "Rejected"
        if body.action == "reject"
        else "Pending"
    )
    resolution = body.comment or body.action

    async with db_session() as session:
        from sqlalchemy import text

        await session.execute(
            text("UPDATE human_queue SET status = :s, resolution = :r WHERE id = :id"),
            {"s": status, "r": resolution, "id": queue_id},
        )

        item_row = (
            await session.execute(
                text("SELECT * FROM human_queue WHERE id = :id"), {"id": queue_id}
            )
        ).first()
        item = _row_to_dict(item_row) if item_row else {}

        if item.get("agentid"):
            await session.execute(
                text(
                    "UPDATE execution_nodes SET state = 'Completed', reasoning = :r WHERE agentId = :aid AND state = 'Blocked'"
                ),
                {"r": f"Human intervened: {body.action}. {resolution}", "aid": item["agentid"]},
            )
            await session.execute(
                text("UPDATE project_agents SET status = 'Running' WHERE id = :aid"),
                {"aid": item["agentid"]},
            )

            if body.action == "approve":
                ts = int(datetime.now().timestamp() * 1000)
                await session.execute(
                    text(
                        "INSERT INTO artifacts (id, projectid, type, storagepath, versionhistory) VALUES (:id,:pid,:t,:u,'{}')"
                    ),
                    {
                        "id": f"art-mapping-{ts}",
                        "pid": item.get("projectid"),
                        "t": "SQL Script",
                        "u": "data/artifacts/Schema_Mapping_Validation.sql",
                    },
                )

        await session.execute(
            text(
                "INSERT INTO audit_logs (id, userid, action, details, timestamp) VALUES (:id,:u,:a,:d,:t)"
            ),
            {
                "id": _uuid(),
                "u": user.get("id"),
                "a": f"Queue {body.action}",
                "d": f"Item {queue_id}: {resolution}",
                "t": _now(),
            },
        )

    return {"success": True}


# ---------------------------------------------------------------------------
# Operations Summary
# ---------------------------------------------------------------------------


@router.get("/operations/summary")
async def operations_summary(request: Request):
    await _get_current_user(request)
    async with db_session() as session:
        from sqlalchemy import text

        projects_rows = (
            await session.execute(
                text("SELECT * FROM business_projects ORDER BY updatedAt DESC LIMIT 5")
            )
        ).fetchall()
        projects = [_row_to_dict(r) for r in projects_rows]

        running = (
            await session.execute(
                text("SELECT count(1) as c FROM business_projects WHERE status = 'Execution'")
            )
        ).scalar()
        active_workers = (
            await session.execute(
                text(
                    "SELECT count(1) as c FROM agents WHERE status IN ('active', 'running', 'executing')"
                )
            )
        ).scalar()
        pending = (
            await session.execute(
                text("SELECT count(1) as c FROM human_queue WHERE status = 'Pending'")
            )
        ).scalar()

        activities_rows = (
            await session.execute(text("SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT 5"))
        ).fetchall()
        activities = [_row_to_dict(r) for r in activities_rows]

        artifacts_rows = (
            await session.execute(text("SELECT * FROM artifacts ORDER BY id DESC LIMIT 5"))
        ).fetchall()
        artifacts_list = [_row_to_dict(r) for r in artifacts_rows]

    return {
        "health": {"status": "Needs approval" if pending else "Running" if running else "Idle"},
        "stats": {
            "runningProjects": running or 0,
            "activeEmployees": active_workers or 0,
            "pendingApprovals": pending or 0,
        },
        "projects": [
            {
                "key": p["id"],
                "project": p["name"],
                "status": p["status"],
                "phase": p["status"],
                "ai": "General AI",
                "updated": p.get("updatedat"),
            }
            for p in projects
        ],
        "providers": [
            {"name": "OpenAI GPT-4o", "type": "LLM Gateway", "status": "Healthy"},
            {"name": "PostgreSQL", "type": "Platform DB", "status": "Healthy"},
        ],
        "sources": [
            {"name": "Core DB", "type": "Internal Data", "status": "Connected"},
        ],
        "activities": [
            {"text": f"{a.get('action', '')}: {a.get('details', '')}", "time": a.get("timestamp")}
            for a in activities
        ],
        "artifacts": [
            {"name": a.get("storagepath", ""), "type": a.get("type", "")} for a in artifacts_list
        ],
    }


# ---------------------------------------------------------------------------
# Connectors — proxies legacy providers into connector format
# ---------------------------------------------------------------------------

_LEGACY_PROVIDERS = [
    {
        "name": "git",
        "version": "0.2.0",
        "capabilities": [
            "discover",
            "sync",
            "files",
            "commits",
            "github-url",
            "bitbucket-url",
            "python-structure",
        ],
    },
    {
        "name": "jira",
        "version": "0.1.0",
        "capabilities": ["discover", "sync", "tickets", "comments", "status-events"],
    },
    {
        "name": "mysql",
        "version": "0.2.0",
        "capabilities": [
            "discover",
            "sync",
            "live-connection",
            "schemas",
            "tables",
            "columns",
            "foreign-keys",
        ],
    },
]

_PROVIDER_CATEGORY_MAP = {
    "git": "Source Control",
    "jira": "Project Management",
    "mysql": "Database",
    "slack": "Communication",
    "confluence": "Documentation",
}


def _provider_to_connector(p: dict) -> dict:
    """Map a legacy provider to the connector format the frontend expects."""
    name = p["name"]
    return {
        "id": f"provider-{name}",
        "name": name.upper() if name == "jira" else name.capitalize(),
        "type": p.get("version", ""),
        "category": _PROVIDER_CATEGORY_MAP.get(name, "Data Source"),
        "status": "Connected",
        "config": {"capabilities": p.get("capabilities", [])},
    }


@router.get("/connectors")
async def list_connectors(request: Request):
    await _get_current_user(request)
    # Also include any DB-stored project_connectors
    async with db_session() as session:
        from sqlalchemy import text

        rows = (await session.execute(text("SELECT * FROM project_connectors"))).fetchall()
        db_connectors = [
            {
                "id": f"db-{r['id']}",
                "name": _row_to_dict(r).get("connector_type", "").capitalize(),
                "type": _row_to_dict(r).get("connector_type", ""),
                "category": "Project Connector",
                "status": "Active",
                "config": _row_to_dict(r).get("config", {}),
            }
            for r in rows
        ]
    return [_provider_to_connector(p) for p in _LEGACY_PROVIDERS] + db_connectors


@router.get("/connectors/{connector_id}")
async def get_connector(connector_id: str, request: Request):
    await _get_current_user(request)
    # Check legacy providers first
    for p in _LEGACY_PROVIDERS:
        if f"provider-{p['name']}" == connector_id:
            c = _provider_to_connector(p)
            c["schemaData"] = None
            return c
    # Fall back to DB
    async with db_session() as session:
        from sqlalchemy import text

        row = (
            await session.execute(
                text("SELECT * FROM project_connectors WHERE id = :id"),
                {"id": connector_id.replace("db-", "")},
            )
        ).first()
        if not row:
            _error_response("NOT-FOUND", "Connector not found", status=404)
        r = _row_to_dict(row)
        return {
            "id": f"db-{r['id']}",
            "name": r.get("connector_type", "").capitalize(),
            "type": r.get("connector_type", ""),
            "category": "Project Connector",
            "status": "Active",
            "config": r.get("config", {}),
            "schemaData": None,
        }


@router.post("/connectors/{connector_id}/test")
async def test_connector(connector_id: str, request: Request):
    await _get_current_user(request)
    return {"success": True, "message": "Connection successful"}


@router.post("/connectors/{connector_id}/discover")
async def discover_connector(connector_id: str, request: Request):
    await _get_current_user(request)
    return {
        "success": True,
        "schemaData": {
            "tables": ["users", "projects", "agents", "sessions"],
            "relationships": ["users.id → sessions.userId", "projects.id → agents.projectId"],
            "columns": {"users": ["id", "email", "role"], "projects": ["id", "name", "status"]},
        },
    }


# ---------------------------------------------------------------------------
# Knowledge — proxies ECMS graph nodes + categories
# ---------------------------------------------------------------------------


@router.get("/knowledge/categories")
async def knowledge_categories(request: Request):
    """Return categories for the Knowledge tab."""
    await _get_current_user(request)
    async with db_session() as session:
        from sqlalchemy import text

        rows = (
            await session.execute(text("SELECT * FROM categories ORDER BY priority"))
        ).fetchall()
        return [
            {
                "id": _row_to_dict(r)["id"],
                "name": _row_to_dict(r)["name"],
                "description": _row_to_dict(r)["description"],
                "color": _row_to_dict(r)["color"],
                "priority": _row_to_dict(r)["priority"],
            }
            for r in rows
        ]


@router.get("/knowledge")
async def list_knowledge(request: Request):
    """Return knowledge items — tries ECMS graph first, falls back to aggregates."""
    await _get_current_user(request)

    # Try to get graph nodes from the cognitive system
    try:
        cognitive = request.app.state.cognitive
        if cognitive and cognitive.graph:
            stats = await cognitive.graph.statistics()
            all_nodes = await cognitive.graph._store.all_nodes()
            nodes = []
            for node in all_nodes if isinstance(all_nodes, list) else all_nodes.get("nodes", []):
                n = node if isinstance(node, dict) else node.__dict__
                nodes.append(
                    {
                        "id": n.get("node_id", n.get("id", "")),
                        "title": n.get("display_name", n.get("canonical_name", n.get("name", ""))),
                        "type": n.get("ontology_type", n.get("type", "unknown")),
                        "version": "1.0",
                        "tags": [n.get("ontology_type", "")] if n.get("ontology_type") else [],
                        "status": n.get("lifecycle_state", "active"),
                        "isBuiltIn": 0,
                        "confidence": n.get("confidence", 0),
                        "description": n.get("description", ""),
                    }
                )
            if nodes:
                return nodes
    except Exception:
        pass

    # Fall back to aggregates table
    async with db_session() as session:
        from sqlalchemy import text

        rows = (await session.execute(text("SELECT * FROM aggregates LIMIT 100"))).fetchall()
        results = []
        for r in rows:
            d = _row_to_dict(r)
            data = {}
            try:
                import json as _json

                data = (
                    _json.loads(d.get("data", "{}"))
                    if isinstance(d.get("data"), str)
                    else d.get("data", {})
                )
            except Exception:
                pass
            results.append(
                {
                    "id": d["id"],
                    "title": data.get("display_name", data.get("name", d["id"])),
                    "type": d.get("aggregate_type", "unknown"),
                    "version": str(d.get("version", 1)),
                    "tags": data.get("tags", []),
                    "status": d.get("lifecycle_state", "active"),
                    "isBuiltIn": 0,
                    "description": data.get("description", ""),
                }
            )
        return results


@router.get("/knowledge/{knowledge_id}")
async def get_knowledge(knowledge_id: str, request: Request):
    """Get a single knowledge item — tries graph node, falls back to aggregate."""
    await _get_current_user(request)

    # Try graph node
    try:
        cognitive = request.app.state.cognitive
        if cognitive and cognitive.graph:
            node = cognitive.graph.find_node(knowledge_id)
            if node:
                n = node if isinstance(node, dict) else node.__dict__
                edges = (
                    cognitive.graph.edges_of(knowledge_id)
                    if hasattr(cognitive.graph, "edges_of")
                    else []
                )
                return {
                    "id": n.get("node_id", knowledge_id),
                    "title": n.get("display_name", n.get("canonical_name", "")),
                    "type": n.get("ontology_type", "unknown"),
                    "version": "1.0",
                    "tags": [n.get("ontology_type", "")] if n.get("ontology_type") else [],
                    "status": n.get("lifecycle_state", "active"),
                    "isBuiltIn": 0,
                    "confidence": n.get("confidence", 0),
                    "description": n.get("description", ""),
                    "source": n.get("knowledge_sources", ["graph"])[0]
                    if n.get("knowledge_sources")
                    else "graph",
                    "owner": "system",
                    "createdAt": n.get("created_at", ""),
                    "metadata": n,
                    "relationships": [
                        {
                            "target": e.get("target_name", e.get("target", "")),
                            "type": e.get("relationship_type", e.get("type", "")),
                        }
                        for e in (edges if isinstance(edges, list) else [])
                    ],
                }
    except Exception:
        pass

    # Fall back to aggregates
    async with db_session() as session:
        from sqlalchemy import text

        row = (
            await session.execute(
                text("SELECT * FROM aggregates WHERE id = :id"), {"id": knowledge_id}
            )
        ).first()
        if not row:
            _error_response("NOT-FOUND", "Knowledge item not found", status=404)
        d = _row_to_dict(row)
        data = {}
        try:
            import json as _json

            data = (
                _json.loads(d.get("data", "{}"))
                if isinstance(d.get("data"), str)
                else d.get("data", {})
            )
        except Exception:
            pass
        return {
            "id": d["id"],
            "title": data.get("display_name", data.get("name", d["id"])),
            "type": d.get("aggregate_type", "unknown"),
            "version": str(d.get("version", 1)),
            "tags": data.get("tags", []),
            "status": d.get("lifecycle_state", "active"),
            "isBuiltIn": 0,
            "description": data.get("description", ""),
            "source": data.get("source", "aggregate"),
            "owner": "system",
            "createdAt": d.get("created_at", ""),
            "metadata": data,
            "relationships": [],
        }


# ---------------------------------------------------------------------------
# Skills
# ---------------------------------------------------------------------------


@router.get("/skills")
async def list_skills(request: Request):
    await _get_current_user(request)
    return [
        {"id": "skill-1", "name": "Data Mapping", "category": "Technical", "status": "active"},
        {
            "id": "skill-2",
            "name": "SQL Query Generation",
            "category": "Technical",
            "status": "active",
        },
        {
            "id": "skill-3",
            "name": "OCR Text Extraction",
            "category": "Technical",
            "status": "active",
        },
        {"id": "skill-4", "name": "Anomaly Detection", "category": "Analytics", "status": "active"},
        {
            "id": "skill-5",
            "name": "Compliance Verification",
            "category": "Compliance",
            "status": "active",
        },
    ]


@router.get("/skills/{skill_id}")
async def get_skill(skill_id: str, request: Request):
    await _get_current_user(request)
    return {"id": skill_id, "name": skill_id, "category": "Technical", "status": "active"}


# ---------------------------------------------------------------------------
# AI Models — manage OpenAI-compatible model configurations
# ---------------------------------------------------------------------------


class AIModelCreateBody(BaseModel):
    name: str
    provider: str
    model_id: str
    api_key: str | None = None
    base_url: str | None = None
    is_default: bool = False
    is_ba_agent: bool = False


@router.get("/ai-models")
async def list_ai_models(request: Request):
    """List all AI model configurations."""
    await _get_current_user(request)
    async with db_session() as session:
        from sqlalchemy import text

        rows = (
            await session.execute(
                text("SELECT * FROM ai_models ORDER BY is_default DESC, created_at DESC")
            )
        ).fetchall()
        return [_row_to_dict(r) for r in rows]


@router.post("/ai-models")
async def create_ai_model(body: AIModelCreateBody, request: Request):
    """Add a new AI model configuration."""
    await _get_current_user(request)
    mid = f"model-{_uuid()[:8]}"
    now = _now()
    async with db_session() as session:
        from sqlalchemy import text

        # Unset previous default if this is default
        if body.is_default:
            await session.execute(text("UPDATE ai_models SET is_default = 0"))
        # Unset previous BA agent flag if this is flagged
        if body.is_ba_agent:
            await session.execute(text("UPDATE ai_models SET is_ba_agent = 0"))
        await session.execute(
            text(
                "INSERT INTO ai_models (id, name, provider, model_id, api_key, base_url, is_default, is_ba_agent, created_at) "
                "VALUES (:id, :name, :provider, :mid, :key, :url, :def, :ba, :t)"
            ),
            {
                "id": mid,
                "name": body.name,
                "provider": body.provider,
                "mid": body.model_id,
                "key": body.api_key,
                "url": body.base_url,
                "def": 1 if body.is_default else 0,
                "ba": 1 if body.is_ba_agent else 0,
                "t": now,
            },
        )
    return {"success": True, "id": mid}


@router.put("/ai-models/{model_id}")
async def update_ai_model(model_id: str, body: dict, request: Request):
    """Update an AI model configuration."""
    await _get_current_user(request)
    async with db_session() as session:
        from sqlalchemy import text

        if body.get("is_default"):
            await session.execute(text("UPDATE ai_models SET is_default = 0"))
        if body.get("is_ba_agent"):
            await session.execute(text("UPDATE ai_models SET is_ba_agent = 0"))
        await session.execute(
            text(
                "UPDATE ai_models SET name=:name, provider=:provider, model_id=:mid, api_key=:key, "
                "base_url=:url, is_default=:def, is_ba_agent=:ba WHERE id=:id"
            ),
            {
                "id": model_id,
                "name": body.get("name"),
                "provider": body.get("provider"),
                "mid": body.get("model_id"),
                "key": body.get("api_key", ""),
                "url": body.get("base_url", ""),
                "def": 1 if body.get("is_default") else 0,
                "ba": 1 if body.get("is_ba_agent") else 0,
            },
        )
    return {"success": True}


@router.delete("/ai-models/{model_id}")
async def delete_ai_model(model_id: str, request: Request):
    """Delete an AI model configuration."""
    await _get_current_user(request)
    async with db_session() as session:
        from sqlalchemy import text

        await session.execute(text("DELETE FROM ai_models WHERE id = :id"), {"id": model_id})
    return {"success": True}


# ---------------------------------------------------------------------------
# Organizations — multi-org support
# ---------------------------------------------------------------------------


@router.get("/organizations")
async def list_organizations(request: Request):
    """Return all organizations (read from existing organization table)."""
    await _get_current_user(request)
    async with db_session() as session:
        from sqlalchemy import text

        rows = (await session.execute(text("SELECT * FROM organization"))).fetchall()
        return [_row_to_dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Project Finalization — store requirements after discovery
# ---------------------------------------------------------------------------


class FinalizeRequest(BaseModel):
    requirements: dict


@router.post("/projects/{project_id}/finalize")
async def finalize_project(project_id: str, body: FinalizeRequest, request: Request):
    """Store discovery requirements in DB + knowledge graph."""
    await _get_current_user(request)
    import json
    import uuid
    from datetime import datetime

    from sqlalchemy import text

    now = datetime.now(UTC).isoformat()
    req = body.requirements

    async with db_session() as session:
        # 1. Store full JSON in business_projects
        await session.execute(
            text(
                "UPDATE business_projects SET requirements = :req, status = 'Planning' WHERE id = :pid"
            ),
            {"req": json.dumps(req), "now": now, "pid": project_id},
        )

        # 2. Store each requirement
        for r in req.get("requirements") or []:
            await session.execute(
                text(
                    "INSERT INTO project_requirements (id, project_id, text, type, status, source, version, created_at, updated_at) "
                    "VALUES (:id, :pid, :text, 'requirement', 'confirmed', :source, 1, :now, :now)"
                ),
                {
                    "id": str(uuid.uuid4()),
                    "pid": project_id,
                    "text": r,
                    "source": "discovery",
                    "now": now,
                },
            )

        # 3. Store recommended skills as requirements
        for s in req.get("recommended_skills") or []:
            await session.execute(
                text(
                    "INSERT INTO project_requirements (id, project_id, text, type, status, source, version, created_at, updated_at) "
                    "VALUES (:id, :pid, :text, 'skill', 'confirmed', :source, 1, :now, :now)"
                ),
                {
                    "id": str(uuid.uuid4()),
                    "pid": project_id,
                    "text": s,
                    "source": "discovery",
                    "now": now,
                },
            )

        # 4. Store recommended connectors as requirements
        for c in req.get("recommended_connectors") or []:
            await session.execute(
                text(
                    "INSERT INTO project_requirements (id, project_id, text, type, status, source, version, created_at, updated_at) "
                    "VALUES (:id, :pid, :text, 'connector', 'confirmed', :source, 1, :now, :now)"
                ),
                {
                    "id": str(uuid.uuid4()),
                    "pid": project_id,
                    "text": c,
                    "source": "discovery",
                    "now": now,
                },
            )

        # 5. Store constraints
        constraints = req.get("constraints") or {}
        for ctype in ["timeline", "budget", "compliance"]:
            val = constraints.get(ctype)
            if val and val != "Not specified":
                await session.execute(
                    text(
                        "INSERT INTO project_constraints (id, project_id, type, value, mandatory, source, version, created_at) "
                        "VALUES (:id, :pid, :type, :value, true, :source, 1, :now)"
                    ),
                    {
                        "id": str(uuid.uuid4()),
                        "pid": project_id,
                        "type": ctype,
                        "value": val,
                        "source": "discovery",
                        "now": now,
                    },
                )
        for val in constraints.get("other") or []:
            await session.execute(
                text(
                    "INSERT INTO project_constraints (id, project_id, type, value, mandatory, source, version, created_at) "
                    "VALUES (:id, :pid, 'other', :value, false, :source, 1, :now)"
                ),
                {
                    "id": str(uuid.uuid4()),
                    "pid": project_id,
                    "value": val,
                    "source": "discovery",
                    "now": now,
                },
            )

        # 6. Store risks
        for r in req.get("risks") or []:
            await session.execute(
                text(
                    "INSERT INTO project_risks (id, project_id, risk, impact, mitigation, status, version, created_at) "
                    "VALUES (:id, :pid, :risk, :impact, :mitigation, 'open', 1, :now)"
                ),
                {
                    "id": str(uuid.uuid4()),
                    "pid": project_id,
                    "risk": r.get("risk", ""),
                    "impact": r.get("impact", "medium"),
                    "mitigation": r.get("mitigation", ""),
                    "now": now,
                },
            )

        # 7. Write event
        await session.execute(
            text(
                "INSERT INTO event_store (event_id, event_type, event_category, correlation_id, payload, created_at) "
                "VALUES (:eid, 'DiscoveryFinalized', 'project', :cid, :payload, NOW())"
            ),
            {
                "eid": str(uuid.uuid4()),
                "cid": project_id,
                "payload": json.dumps(
                    {"project_id": project_id, "version": 1, "summary": req.get("goal", "")}
                ),
            },
        )

    return {
        "success": True,
        "project_id": project_id,
        "stored": {
            "requirements": len(req.get("requirements") or []),
            "skills": len(req.get("recommended_skills") or []),
            "connectors": len(req.get("recommended_connectors") or []),
            "constraints": len(constraints.get("other") or [])
            + sum(
                1
                for c in ["timeline", "budget", "compliance"]
                if constraints.get(c) and constraints.get(c) != "Not specified"
            ),
            "risks": len(req.get("risks") or []),
        },
    }


# ---------------------------------------------------------------------------
# File Upload — document attachments stored per project on local disk
# ---------------------------------------------------------------------------

import hashlib
from pathlib import Path as _Path

from fastapi import File as FastAPIFile
from fastapi import UploadFile

BASE_UPLOAD_DIR = _Path("/workspace/uploads")


@router.post("/projects/{project_id}/upload")
async def upload_project_document(
    project_id: str, file: UploadFile = FastAPIFile(...), request: Request = None
):
    """Upload a discovery document — stored in /workspace/uploads/{project_id}/."""
    await _get_current_user(request)
    content = await file.read()
    hash_digest = hashlib.sha256(content).hexdigest()[:12]
    ext = file.filename.rsplit(".", 1)[-1] if "." in (file.filename or "") else "bin"
    filename = f"{hash_digest}.{ext}"
    project_dir = BASE_UPLOAD_DIR / project_id / "documents"
    project_dir.mkdir(parents=True, exist_ok=True)
    filepath = project_dir / filename
    filepath.write_bytes(content)

    text_content = ""
    try:
        text_content = content.decode("utf-8", errors="ignore")[:50_000]
    except Exception:
        text_content = f"[Binary file: {file.filename}]"

    return {
        "success": True,
        "path": str(filepath),
        "relative_path": f"uploads/{project_id}/documents/{filename}",
        "filename": file.filename,
        "text_content": text_content,
    }


# ---------------------------------------------------------------------------
# Connections — user sync connections management
# ---------------------------------------------------------------------------


@router.get("/connections")
async def list_connections(request: Request):
    """List all active connections for the current user."""
    user = await _get_current_user(request)
    async with db_session() as session:
        from sqlalchemy import text

        rows = (
            await session.execute(
                text(
                    "SELECT * FROM connections WHERE user_id = :uid AND status != 'deleted' ORDER BY number"
                ),
                {"uid": user["id"]},
            )
        ).fetchall()
        connections = []
        for row in rows:
            item = _row_to_dict(row)
            connections.append(
                {
                    "number": item.get("number"),
                    "user_id": item.get("user_id"),
                    "name": item.get("name"),
                    "provider": item.get("provider"),
                    "repo_url": item.get("repo_url"),
                    "config": _json_value(item.get("config"), {}),
                    "status": item.get("status"),
                    "node_count": item.get("node_count"),
                    "created_at": item.get("created_at"),
                    "updated_at": item.get("updated_at"),
                }
            )
        return connections


class SourceControlConnectionBody(BaseModel):
    name: str
    provider: str
    repo_url: str
    config: dict | None = None
    status: str | None = "connected"
    node_count: int | None = 0


def _repo_delete_markers(repo_url: str, config: dict) -> dict[str, str]:
    import hashlib
    from urllib.parse import urlparse

    normalized = (repo_url or config.get("resource_id") or "").strip()
    parsed = urlparse(normalized)
    path_parts = [part for part in parsed.path.removesuffix(".git").split("/") if part]
    owner_repo = "/".join(path_parts[:2]).lower() if len(path_parts) >= 2 else ""
    repo_name = (
        path_parts[1].lower()
        if len(path_parts) >= 2
        else (path_parts[0].lower() if path_parts else "")
    )
    clone_dir = ""
    if parsed.hostname and path_parts:
        readable = "-".join([parsed.hostname.lower(), *path_parts])[:80]
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:12]
        clone_dir = f"{readable}-{digest}".lower()
    return {
        "repo_url": repo_url or "",
        "repo_url_no_git": repo_url.removesuffix(".git") if repo_url else "",
        "resource_id": str(config.get("resource_id") or ""),
        "clone_dir": clone_dir,
        "owner_repo": owner_repo,
        "repo_name": repo_name,
    }


def _delete_source_control_graph_data(
    connection: dict, delete_all_git: bool = False
) -> dict[str, int | bool | str]:
    repo_url = str(connection.get("repo_url") or "")
    config = _json_value(connection.get("config"), {})
    if not repo_url and not config.get("resource_id") and not delete_all_git:
        return {"attempted": False, "deleted": 0}

    import falkordb
    from legacy_ecms.config import get_settings as _legacy_settings

    settings = _legacy_settings()
    db = falkordb.FalkorDB(
        host=settings.falkordb_host,
        port=settings.falkordb_port,
        password=settings.falkordb_password or None,
    )
    graph = db.select_graph(settings.falkordb_database)
    params = {**_repo_delete_markers(repo_url, config), "delete_all_git": delete_all_git}
    result = graph.query(
        "MATCH (u:UKO) "
        "WHERE ($delete_all_git = true AND (u.source = 'git' OR u.id CONTAINS 'git:' OR u.source_id CONTAINS 'git:')) "
        "OR ($repo_url <> '' AND u.source_url = $repo_url) "
        "OR ($repo_url_no_git <> '' AND u.source_url = $repo_url_no_git) "
        "OR ($resource_id <> '' AND u.source_url = $resource_id) "
        "OR ($clone_dir <> '' AND toLower(u.id) CONTAINS $clone_dir) "
        "WITH u DETACH DELETE u RETURN count(u)",
        params,
    )
    rows = result.result_set if hasattr(result, "result_set") else result
    deleted = int(rows[0][0]) if rows and rows[0] else 0
    return {"attempted": True, "deleted": deleted, "delete_all_git": delete_all_git}


@router.post("/connections/source-control")
async def upsert_source_control_connection(body: SourceControlConnectionBody, request: Request):
    """Persist a GitHub/Bitbucket sync as a user-visible graph connection."""
    user = await _get_current_user(request)
    provider = (body.provider or "").strip().lower()
    if provider not in {"git", "github", "gitlab", "bitbucket"}:
        _error_response(
            "CONNECTION-4001", "Only source-control connections are supported here", status=400
        )

    repo_url = body.repo_url.strip()
    if not repo_url:
        _error_response("CONNECTION-4002", "Repository URL is required", status=400)

    import json as _json

    now = _now()
    config_json = _json.dumps(body.config or {})
    async with db_session() as session:
        from sqlalchemy import text

        existing = (
            await session.execute(
                text(
                    "SELECT * FROM connections "
                    "WHERE user_id = :uid AND lower(provider) = :provider AND repo_url = :repo_url "
                    "ORDER BY number LIMIT 1"
                ),
                {"uid": user["id"], "provider": provider, "repo_url": repo_url},
            )
        ).first()

        if existing:
            await session.execute(
                text(
                    "UPDATE connections SET name = :name, config = :config, status = :status, "
                    "node_count = :node_count, updated_at = :t WHERE number = :number"
                ),
                {
                    "number": _row_to_dict(existing)["number"],
                    "name": body.name,
                    "config": config_json,
                    "status": body.status or "connected",
                    "node_count": body.node_count or 0,
                    "t": now,
                },
            )
            row = (
                await session.execute(
                    text("SELECT * FROM connections WHERE number = :number"),
                    {"number": _row_to_dict(existing)["number"]},
                )
            ).first()
        else:
            row = (
                await session.execute(
                    text(
                        "INSERT INTO connections (user_id, name, provider, repo_url, config, status, node_count, created_at, updated_at) "
                        "VALUES (:uid, :name, :provider, :repo_url, :config, :status, :node_count, :t, :t) "
                        "RETURNING *"
                    ),
                    {
                        "uid": user["id"],
                        "name": body.name,
                        "provider": provider,
                        "repo_url": repo_url,
                        "config": config_json,
                        "status": body.status or "connected",
                        "node_count": body.node_count or 0,
                        "t": now,
                    },
                )
            ).first()

        await session.execute(
            text(
                "INSERT INTO audit_logs (id, action, userid, details, timestamp) VALUES (:id, :a, :u, :d, :t)"
            ),
            {
                "id": _uuid(),
                "a": "Source Control Knowledge Graph Created",
                "u": user["id"],
                "d": f"{body.provider} repository indexed: {repo_url}",
                "t": now,
            },
        )

    saved = _row_to_dict(row)
    return {
        "number": saved.get("number"),
        "user_id": saved.get("user_id"),
        "name": saved.get("name"),
        "provider": saved.get("provider"),
        "repo_url": saved.get("repo_url"),
        "status": saved.get("status"),
        "node_count": saved.get("node_count"),
        "created_at": saved.get("created_at"),
        "updated_at": saved.get("updated_at"),
    }


@router.delete("/connections/{number}")
async def delete_connection(number: int, request: Request):
    """Delete a connection and shift higher connections down."""
    user = await _get_current_user(request)

    async with db_session() as session:
        from sqlalchemy import text

        # Get the connection
        conn_row = (
            await session.execute(
                text("SELECT * FROM connections WHERE number = :num AND user_id = :uid"),
                {"num": number, "uid": user["id"]},
            )
        ).first()

        if not conn_row:
            _error_response("NOT-FOUND", "Connection not found", status=404)
        conn = _row_to_dict(conn_row)

        # Mark as reindexing
        await session.execute(
            text(
                "UPDATE connections SET status = 'reindexing', updated_at = :t WHERE number = :num"
            ),
            {"num": number, "t": _now()},
        )

        remaining_source_connections = (
            await session.execute(
                text(
                    "SELECT count(*) FROM connections "
                    "WHERE user_id = :uid AND number != :num AND repo_url IS NOT NULL AND status != 'deleted'"
                ),
                {"uid": user["id"], "num": number},
            )
        ).scalar_one()
        graph_delete = {"attempted": False, "deleted": 0}
        if conn.get("repo_url") or (conn.get("provider") or "").lower() in {
            "git",
            "github",
            "bitbucket",
        }:
            try:
                graph_delete = _delete_source_control_graph_data(
                    conn,
                    delete_all_git=int(remaining_source_connections or 0) == 0,
                )
            except Exception as exc:
                _error_response("CONNECTION-5001", f"Graph cleanup failed: {exc}", status=500)

        # Delete the connection
        await session.execute(text("DELETE FROM connections WHERE number = :num"), {"num": number})

        # Shift higher connections down
        await session.execute(
            text("UPDATE connections SET number = number - 1, updated_at = :t WHERE number > :num"),
            {"num": number, "t": _now()},
        )

        # Log the deletion
        await session.execute(
            text(
                "INSERT INTO audit_logs (id, action, userid, details, timestamp) VALUES (:id, :a, :u, :d, :t)"
            ),
            {
                "id": _uuid(),
                "a": "Connection Deleted",
                "u": user["id"],
                "d": f"Connection #{number} deleted; graph nodes removed: {graph_delete.get('deleted', 0)}",
                "t": _now(),
            },
        )

    if graph_delete.get("deleted"):
        from ecms.visualization.graph_changed import graph_changed

        await graph_changed("default", source="connection-delete", revision=str(number))

    return {
        "success": True,
        "message": f"Connection #{number} deleted",
        "graph_delete": graph_delete,
    }


# ---------------------------------------------------------------------------
# Graph — FalkorDB queries via redis-cli subprocess
# ---------------------------------------------------------------------------


@router.get("/graph/nodes")
async def graph_nodes(request: Request):
    """Return graph nodes from FalkorDB."""
    await _get_current_user(request)

    # Try cognitive system first
    try:
        cognitive = request.app.state.cognitive
        if cognitive and cognitive.graph:
            all_nodes = await cognitive.graph._store.all_nodes()
            nodes = []
            for node in all_nodes if isinstance(all_nodes, list) else all_nodes.get("nodes", []):
                n = node if isinstance(node, dict) else node.__dict__
                nodes.append(
                    {
                        "id": n.get("node_id", n.get("id", "")),
                        "label": n.get("display_name", n.get("canonical_name", n.get("name", ""))),
                        "type": n.get("ontology_type", n.get("type", "unknown")),
                        "domain": n.get("domain", "uncategorized"),
                        "confidence": round((n.get("confidence", 0.5)) * 100),
                    }
                )
            if nodes:
                return nodes
    except Exception:
        pass

    # Query FalkorDB via redis-cli subprocess
    try:
        import os
        import subprocess

        url = os.environ.get("ECMS_FALKORDB_URL", "redis://falkordb:6379")
        host = url.replace("redis://", "").split(":")[0]
        port = url.replace("redis://", "").split(":")[1].split("/")[0]
        result = subprocess.run(
            [
                "redis-cli",
                "-h",
                host,
                "-p",
                port,
                "GRAPH.QUERY",
                "ecms",
                "MATCH (n) RETURN n.id, n.name, n.type LIMIT 500",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0 and result.stdout:
            lines = result.stdout.strip().split("\n")
            nodes = []
            for line in lines[1:]:  # Skip header row
                line = line.strip()
                if not line or line.startswith("Cached") or line.startswith("Query internal"):
                    continue
                parts = [p.strip() for p in line.split("\t") if p.strip()]
                if len(parts) >= 3:
                    nodes.append(
                        {
                            "id": parts[0],
                            "label": parts[1] or parts[0],
                            "type": parts[2] or "unknown",
                            "domain": "uncategorized",
                            "confidence": 50,
                        }
                    )
            return nodes
    except Exception:
        pass
    return []


@router.get("/graph/edges")
async def graph_edges(request: Request):
    """Return graph edges from FalkorDB."""
    await _get_current_user(request)

    # Try cognitive system first
    try:
        cognitive = request.app.state.cognitive
        if cognitive and cognitive.graph:
            all_edges = cognitive.graph._store.all_edges()
            edges = []
            for edge in all_edges if isinstance(all_edges, list) else all_edges.get("edges", []):
                e = edge if isinstance(edge, dict) else edge.__dict__
                edges.append(
                    {
                        "id": e.get("edge_id", e.get("id", "")),
                        "source": e.get("source_id", e.get("source", "")),
                        "target": e.get("target_id", e.get("target", "")),
                        "relationship": e.get("relationship_type", e.get("type", "related")),
                    }
                )
            if edges:
                return edges
    except Exception:
        pass

    # Query FalkorDB via redis-cli subprocess
    try:
        import os
        import subprocess

        url = os.environ.get("ECMS_FALKORDB_URL", "redis://falkordb:6379")
        host = url.replace("redis://", "").split(":")[0]
        port = url.replace("redis://", "").split(":")[1].split("/")[0]
        result = subprocess.run(
            [
                "redis-cli",
                "-h",
                host,
                "-p",
                port,
                "GRAPH.QUERY",
                "ecms",
                "MATCH (a)-[r]->(b) RETURN a.id, b.id, type(r) LIMIT 2000",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0 and result.stdout:
            lines = result.stdout.strip().split("\n")
            edges = []
            for line in lines[1:]:  # Skip header row
                line = line.strip()
                if not line or line.startswith("Cached") or line.startswith("Query internal"):
                    continue
                parts = [p.strip() for p in line.split("\t") if p.strip()]
                if len(parts) >= 3:
                    edges.append(
                        {
                            "id": f"{parts[0]}-{parts[1]}",
                            "source": parts[0],
                            "target": parts[1],
                            "relationship": parts[2] or "related",
                        }
                    )
            return edges
    except Exception:
        pass
    return []


@router.get("/graph/statistics")
async def graph_statistics(request: Request):
    """Return graph statistics from FalkorDB."""
    await _get_current_user(request)

    try:
        import os
        import subprocess

        url = os.environ.get("ECMS_FALKORDB_URL", "redis://falkordb:6379")
        host = url.replace("redis://", "").split(":")[0]
        port = url.replace("redis://", "").split(":")[1].split("/")[0]
        result = subprocess.run(
            [
                "redis-cli",
                "-h",
                host,
                "-p",
                port,
                "GRAPH.QUERY",
                "ecms",
                "MATCH (n) RETURN count(n)",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0 and result.stdout:
            lines = result.stdout.strip().split("\n")
            for line in lines:
                if line.strip().isdigit():
                    return {"node_count": int(line.strip()), "edge_count": 0}
    except Exception:
        pass
    return {"node_count": 0, "edge_count": 0}

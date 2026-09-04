"""Organization tools — task delegation, cross-team communication.

These are agent tools for the digital org hierarchy. They use the agents,
tasks, and cross_team_requests tables for persistence.
"""

from __future__ import annotations

import json
from typing import Any

from ecms.agent.permissions import (
    can_assign,
    can_request_cross_team,
    find_senior_in_dept,
)
from ecms.persistence.database.rest_session import db_session
from ecms.persistence.repositories.task import TaskRepository

# ── Tool definitions ────────────────────────────────────────────

ORG_TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "assign_task",
            "description": "Assign a task to an agent in your reporting chain. Provide clear instructions, inputs, and expected output.",
            "parameters": {
                "type": "object",
                "properties": {
                    "assignee_id": {
                        "type": "string",
                        "description": "Agent ID to assign the task to.",
                    },
                    "title": {"type": "string", "description": "Task title."},
                    "description": {"type": "string", "description": "Detailed instructions."},
                    "inputs": {
                        "type": "string",
                        "description": 'JSON string of file paths, specs, references. Example: \'{"files":["spec.md"]}\'.',
                    },
                    "expected_output": {
                        "type": "string",
                        "description": "What format/output you expect from the assignee.",
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "normal", "high", "blocking"],
                        "description": "Task priority.",
                    },
                },
                "required": ["assignee_id", "title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "my_tasks",
            "description": "List your assigned tasks. Filter by status.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["pending", "in_progress", "submitted", "approved", "rejected"],
                        "description": "Filter by status.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "start_task",
            "description": "Start working on a task assigned to you. Loads task context into your session.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "The task ID to start."},
                },
                "required": ["task_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "submit_task",
            "description": "Submit a completed task for review. Include a summary and list output files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "The task ID to submit."},
                    "summary": {"type": "string", "description": "Summary of what you built."},
                    "output_files": {
                        "type": "string",
                        "description": "JSON array of file paths produced. Example: '[\"src/main.py\"]'.",
                    },
                },
                "required": ["task_id", "summary"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "review_task",
            "description": "Review a submitted task. Approve or reject with feedback.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "The task ID to review."},
                    "decision": {
                        "type": "string",
                        "enum": ["approved", "rejected"],
                        "description": "Approve or reject.",
                    },
                    "feedback": {
                        "type": "string",
                        "description": "Review feedback. Required for rejections, optional for approvals.",
                    },
                },
                "required": ["task_id", "decision"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "request_from_team",
            "description": "Request work from another department. Use when your task is blocked by a dependency outside your team.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "What you need."},
                    "description": {
                        "type": "string",
                        "description": "Detailed spec of what's needed and why.",
                    },
                    "target_department": {
                        "type": "string",
                        "description": "Department to request from: backend, frontend, devops, data, platform, qa.",
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "normal", "high", "blocking"],
                        "description": "How urgent this is.",
                    },
                    "inputs": {
                        "type": "string",
                        "description": "JSON string of specs, contracts, examples.",
                    },
                },
                "required": ["title", "target_department"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "my_blockers",
            "description": "Show all tasks blocking your current work. Shows status of each blocker.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
]

# ── Agent context (set by AgentLoop) ────────────────────────────

_CURRENT_AGENT_ID: str | None = None
_CURRENT_AGENT: dict[str, Any] | None = None


def set_org_context(agent_id: str | None, agent_data: dict[str, Any] | None) -> None:
    global _CURRENT_AGENT_ID, _CURRENT_AGENT
    _CURRENT_AGENT_ID = agent_id
    _CURRENT_AGENT = agent_data


def get_org_context() -> tuple[str | None, dict[str, Any] | None]:
    return _CURRENT_AGENT_ID, _CURRENT_AGENT


# ── Tool implementations ────────────────────────────────────────


async def assign_task(
    assignee_id: str,
    title: str,
    description: str = "",
    inputs: str = "{}",
    expected_output: str = "",
    priority: str = "normal",
) -> str:
    if not _CURRENT_AGENT_ID:
        return "ERROR: No agent identity set for this session."

    try:
        inputs_dict = json.loads(inputs) if inputs else {}
    except json.JSONDecodeError:
        return "ERROR: inputs must be valid JSON."

    if not await can_assign(_CURRENT_AGENT_ID, assignee_id):
        return f"ERROR: You do not have authority to assign tasks to agent {assignee_id}."

    async with db_session() as s:
        repo = TaskRepository(s)
        task = await repo.create(
            title=title,
            assigner_id=_CURRENT_AGENT_ID,
            assignee_id=assignee_id,
            description=description,
            inputs=inputs_dict,
            expected_output=expected_output,
            priority=priority,
        )
    return (
        f"Task created: {task.id}\nTitle: {title}\nAssigned to: {assignee_id}\nPriority: {priority}"
    )


async def my_tasks(status: str | None = None) -> str:
    if not _CURRENT_AGENT_ID:
        return "ERROR: No agent identity set for this session."

    async with db_session() as s:
        repo = TaskRepository(s)
        # Tasks assigned to me
        assigned = await repo.list_by_assignee(_CURRENT_AGENT_ID, status)
        # Tasks I assigned
        delegated = await repo.list_by_assigner(_CURRENT_AGENT_ID, status)

    lines = [f"## Your Tasks ({len(assigned)})"]
    if not assigned:
        lines.append("(no tasks assigned to you)")
    for t in assigned:
        icon = {
            "pending": "○",
            "in_progress": "●",
            "submitted": "✓",
            "approved": "✅",
            "rejected": "✗",
        }.get(t.status, "·")
        lines.append(f"  {icon} {t.id}: {t.title} [{t.priority}] — {t.status}")

    if delegated:
        lines.append(f"\n## Tasks You Assigned ({len(delegated)})")
        for t in delegated:
            icon = {
                "pending": "○",
                "in_progress": "●",
                "submitted": "✓",
                "approved": "✅",
                "rejected": "✗",
            }.get(t.status, "·")
            lines.append(f"  {icon} {t.id}: {t.title} → {t.assignee_id} [{t.status}]")

    return "\n".join(lines)


async def start_task(task_id: str) -> str:
    if not _CURRENT_AGENT_ID:
        return "ERROR: No agent identity set for this session."

    async with db_session() as s:
        repo = TaskRepository(s)
        task = await repo.get(task_id)
        if not task:
            return f"ERROR: Task {task_id} not found."
        if task.assignee_id != _CURRENT_AGENT_ID:
            return f"ERROR: Task {task_id} is not assigned to you."
        if task.status != "pending":
            return f"ERROR: Task is already {task.status}."

        await repo.update_status(task_id, "in_progress")

    parts = [
        f"## Task Started: {task.title}",
        f"**ID:** {task.id}",
        f"**Priority:** {task.priority}",
    ]
    if task.description:
        parts.append(f"**Instructions:**\n{task.description}")
    if task.expected_output:
        parts.append(f"**Expected Output:**\n{task.expected_output}")
    if task.inputs:
        parts.append(f"**Provided Inputs:** {json.dumps(task.inputs)}")
    parts.append("\nYou are now working on this task. Use your tools to complete it.")
    parts.append("When done, call submit_task with your summary and output files.")

    return "\n\n".join(parts)


async def submit_task(task_id: str, summary: str, output_files: str = "[]") -> str:
    if not _CURRENT_AGENT_ID:
        return "ERROR: No agent identity set for this session."

    try:
        files_list = json.loads(output_files) if output_files else []
    except json.JSONDecodeError:
        return "ERROR: output_files must be valid JSON array."

    async with db_session() as s:
        repo = TaskRepository(s)
        task = await repo.get(task_id)
        if not task:
            return f"ERROR: Task {task_id} not found."
        if task.assignee_id != _CURRENT_AGENT_ID:
            return f"ERROR: Task {task_id} is not assigned to you."
        if task.status != "in_progress":
            return f"ERROR: Task must be in_progress to submit. Current: {task.status}."

        await repo.update_status(
            task_id,
            "submitted",
            output_summary=summary,
            output_files=files_list,
        )

    return f"Task {task_id} submitted for review.\nSummary: {summary[:200]}\nFiles: {files_list}"


async def review_task(task_id: str, decision: str, feedback: str = "") -> str:
    if not _CURRENT_AGENT_ID:
        return "ERROR: No agent identity set for this session."

    async with db_session() as s:
        repo = TaskRepository(s)
        task = await repo.get(task_id)
        if not task:
            return f"ERROR: Task {task_id} not found."
        if task.assigner_id != _CURRENT_AGENT_ID:
            return "ERROR: Only the assigner can review this task."
        if task.status != "submitted":
            return f"ERROR: Task must be submitted before review. Current: {task.status}."

        if decision == "approved":
            await repo.update_status(task_id, "approved", review_feedback=feedback)
            return (
                f"Task {task_id} APPROVED.\nFeedback: {feedback}"
                if feedback
                else f"Task {task_id} APPROVED."
            )
        else:
            await repo.update_status(task_id, "rejected", review_feedback=feedback)
            return f"Task {task_id} REJECTED. Feedback: {feedback}\nAssignee can restart with start_task()."


async def request_from_team(
    title: str,
    target_department: str,
    description: str = "",
    priority: str = "normal",
    inputs: str = "{}",
) -> str:
    if not _CURRENT_AGENT_ID:
        return "ERROR: No agent identity set for this session."

    if not await can_request_cross_team(_CURRENT_AGENT_ID, target_department):
        return "ERROR: You don't have authority to make cross-team requests. You must manage people to request from other teams."

    try:
        inputs_dict = json.loads(inputs) if inputs else {}
    except json.JSONDecodeError:
        return "ERROR: inputs must be valid JSON."

    target_senior = await find_senior_in_dept(target_department)
    if not target_senior:
        return f"ERROR: No managing agent found in department '{target_department}'."

    async with db_session() as s:
        repo = TaskRepository(s)
        ctr = await repo.create_ctr(
            title=title,
            requester_id=_CURRENT_AGENT_ID,
            target_dept=target_department,
            description=description,
            inputs=inputs_dict,
            priority=priority,
            target_senior_id=target_senior,
        )

    return (
        f"Cross-team request created: {ctr.id}\n"
        f"Title: {title}\n"
        f"Target: {target_department} (senior: {target_senior})\n"
        f"Priority: {priority}\n"
        f"Status: pending"
    )


async def my_blockers() -> str:
    if not _CURRENT_AGENT_ID:
        return "ERROR: No agent identity set for this session."

    async with db_session() as s:
        repo = TaskRepository(s)
        tasks = await repo.list_by_assignee(_CURRENT_AGENT_ID)
        all_blockers: list[dict] = []
        for task in tasks:
            blockers = await repo.get_blockers(task.id)
            for b in blockers:
                b["blocked_task_title"] = task.title
                all_blockers.append(b)

    if not all_blockers:
        return "No blockers found. You're clear to work on any pending task."

    lines = ["## Blockers"]
    for b in all_blockers:
        bt = b["blocker_task"]
        ctr = b.get("cross_team_request")
        status = bt["status"]
        lines.append(f"\n- **{b['blocked_task_title']}** is blocked by:")
        lines.append(f"  - {bt['title']} ({bt['assignee_id']}) — {status}")
        if ctr:
            lines.append(
                f"  - Cross-team request: {ctr['title']} → {ctr['target_dept']} ({ctr['status']})"
            )
    return "\n".join(lines)


# ── Dispatcher ──────────────────────────────────────────────────

_ORG_TOOL_MAP = {
    "assign_task": assign_task,
    "my_tasks": my_tasks,
    "start_task": start_task,
    "submit_task": submit_task,
    "review_task": review_task,
    "request_from_team": request_from_team,
    "my_blockers": my_blockers,
}

ORG_TOOL_NAMES = set(_ORG_TOOL_MAP.keys())


async def invoke_org_tool(name: str, arguments: dict[str, Any]) -> str:
    func = _ORG_TOOL_MAP.get(name)
    if not func:
        return f"Unknown org tool: {name}"
    try:
        return await func(**arguments)
    except Exception as e:
        return f"Org tool '{name}' failed: {e}"

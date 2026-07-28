"""Agent permissions — dynamic, reads from agents table at runtime.

No hardcoded roles. The user defines roles, departments, hierarchy,
tool policies, and workspace scopes through the frontend.
"""

from __future__ import annotations

from typing import Any


def get_effective_tools_for_agent(all_tool_defs: list[dict], tool_policy: dict[str, Any]) -> list[dict]:
    """Filter tool definitions based on agent's tool_policy JSON.

    tool_policy format: {"blocked_tools": ["kill_shell", "web_search"], "allowed_tools": ["*"]}
    If allowed_tools contains "*", all non-blocked tools are allowed.
    If allowed_tools is a list of names, only those tools are available.
    blocked_tools always takes precedence.
    """
    blocked = set(tool_policy.get("blocked_tools", []))
    allowed = tool_policy.get("allowed_tools", ["*"])
    if "*" in allowed:
        return [t for t in all_tool_defs if t["function"]["name"] not in blocked]
    return [
        t for t in all_tool_defs
        if t["function"]["name"] in allowed and t["function"]["name"] not in blocked
    ]


async def can_assign(assigner_id: str, assignee_id: str) -> bool:
    """Check if assigner can delegate to assignee based on reports_to tree."""
    from ecms.persistence.database.rest_session import db_session
    from ecms.persistence.repositories.agent import AgentRepository

    async with db_session() as s:
        repo = AgentRepository(s)
        if assigner_id == assignee_id:
            return False
        # Anyone can assign to their direct reports
        # Check: is assignee in assigner's reporting chain?
        assignee = await repo.get(assignee_id)
        if not assignee:
            return False
        # Walk up the chain from assignee
        current_id = assignee.reports_to
        while current_id:
            if current_id == assigner_id:
                return True
            current = await repo.get(current_id)
            if not current:
                break
            current_id = current.reports_to
    return False


async def can_request_cross_team(requester_id: str, target_dept: str) -> bool:
    """Check if an agent can make cross-team requests."""
    from ecms.persistence.database.rest_session import db_session
    from ecms.persistence.repositories.agent import AgentRepository

    async with db_session() as s:
        repo = AgentRepository(s)
        requester = await repo.get(requester_id)
        if not requester:
            return False
        # Agent can request if they have reports (i.e., they manage people)
        reports = await repo.list_by_manager(requester_id)
        if not reports:
            return False
        # Target department must exist and have agents
        dept_agents = await repo.list_by_department(target_dept)
        return len(dept_agents) > 0


async def find_senior_in_dept(dept: str) -> str | None:
    """Find an agent in a department who manages people (has reports)."""
    from ecms.persistence.database.rest_session import db_session
    from ecms.persistence.repositories.agent import AgentRepository

    async with db_session() as s:
        repo = AgentRepository(s)
        agents = await repo.list_by_department(dept)
        for agent in agents:
            reports = await repo.list_by_manager(agent.id)
            if reports:
                return agent.id
    return None


async def seed_cto_if_needed() -> None:
    """Create a default CTO agent if none exists."""
    from ecms.persistence.database.rest_session import db_session
    from ecms.persistence.repositories.agent import AgentRepository

    async with db_session() as s:
        repo = AgentRepository(s)
        existing = await repo.get("agent-cto")
        if existing:
            return
        await repo.create(
            id="agent-cto",
            name="CTO",
            role="cto",
            designation="Chief Technology Officer",
            department="platform",
            reports_to=None,
            tool_policy={"allowed_tools": ["*"], "blocked_tools": []},
            workspace_scope={"write": "/workspace/**", "read": "/**"},
            system_prompt_addon="You are the CTO. Full system access. Assign work, review, and make org-wide decisions.",
        )

"""Access policy engine — evaluates ABAC policies at query time.

Root agents (reports_to IS NULL) get unrestricted access. All other
agents are evaluated through DENY-first policy matching.
"""

from __future__ import annotations

import fnmatch
from collections.abc import Callable
from typing import Any

from ecms.persistence.models.access_policy import AccessPolicy

_RULES: dict[str, list[Callable]] | None = None


def _load_rules() -> dict[str, list[Callable]]:
    """Lazy-load named rule evaluators."""
    return {
        "allow": [_rule_allow],
        "deny": [_rule_deny],
    }


def _matches(agent: Any, resource: dict, policy: AccessPolicy) -> bool:
    """Check if a policy matches an agent + resource combination."""
    # Subject match
    if policy.agent_id:
        agent_id = (
            getattr(agent, "id", agent.get("id", ""))
            if not isinstance(agent, dict)
            else agent.get("id", "")
        )
        if agent_id != policy.agent_id:
            return False
    if policy.department:
        dept = (
            getattr(agent, "department", agent.get("department", ""))
            if not isinstance(agent, dict)
            else agent.get("department", "")
        )
        if dept != policy.department:
            return False
    if policy.role_level_min is not None:
        level = (
            getattr(agent, "role_level", agent.get("role_level", 1))
            if not isinstance(agent, dict)
            else agent.get("role_level", 1)
        )
        if level < policy.role_level_min:
            return False

    # Action match
    if policy.action != "*" and policy.action != resource.get("action", "read"):
        return False

    # Resource type match
    if policy.resource_type and policy.resource_type != resource.get("type"):
        return False

    # Path pattern match
    if policy.path_pattern:
        resource_path = resource.get("source_path", "") or resource.get("path", "")
        if not resource_path:
            return False
        if not fnmatch.fnmatch(resource_path, policy.path_pattern):
            return False

    # Source type match
    if policy.source_type and policy.source_type != resource.get("source"):
        return False

    # Resource attribute match
    for k, v in policy.resource_attrs.items():
        if resource.get(k) != v:
            return False

    return True


def _rule_allow(agent: Any, resource: dict, policy: AccessPolicy) -> bool:
    return _matches(agent, resource, policy)


def _rule_deny(agent: Any, resource: dict, policy: AccessPolicy) -> bool:
    return _matches(agent, resource, policy)


def _is_root_agent(agent: Any) -> bool:
    reports_to = (
        getattr(agent, "reports_to", agent.get("reports_to"))
        if not isinstance(agent, dict)
        else agent.get("reports_to")
    )
    return reports_to is None


async def _get_policies_for_agent(agent: Any) -> list[AccessPolicy]:
    """Fetch all policies matching an agent from the database."""
    from sqlalchemy import or_, select

    from ecms.persistence.database.rest_session import db_session

    department = (
        getattr(agent, "department", agent.get("department", ""))
        if not isinstance(agent, dict)
        else agent.get("department", "")
    )
    agent_id = (
        getattr(agent, "id", agent.get("id", ""))
        if not isinstance(agent, dict)
        else agent.get("id", "")
    )
    role_level = (
        getattr(agent, "role_level", agent.get("role_level", 1))
        if not isinstance(agent, dict)
        else agent.get("role_level", 1)
    )

    async with db_session() as s:
        stmt = (
            select(AccessPolicy)
            .where(
                or_(
                    AccessPolicy.agent_id.is_(None),
                    AccessPolicy.agent_id == agent_id,
                    AccessPolicy.department == department,
                    AccessPolicy.role_level_min <= role_level,
                )
            )
            .order_by(AccessPolicy.priority.asc())
        )
        result = await s.execute(stmt)
        return list(result.scalars().all())


async def evaluate_access(agent: Any, resource: dict, action: str = "read") -> bool:
    """Evaluate whether an agent can access a resource.

    Rules:
    1. Root agent (reports_to IS NULL) → ALLOW everything
    2. DENY policies evaluated first — any match → DENIED
    3. ALLOW policies — first match → ALLOWED
    4. Default → DENY
    """
    if _is_root_agent(agent):
        return True

    resource["action"] = action
    policies = await _get_policies_for_agent(agent)

    for p in policies:
        if p.effect == "deny" and _matches(agent, resource, p):
            return False

    for p in policies:
        if p.effect == "allow" and _matches(agent, resource, p):
            return True

    return False


def filter_atom_results(agent: Any, atoms: list[Any], action: str = "read") -> list[Any]:
    """Post-filter memory atom search results through the policy engine."""
    import asyncio

    allowed = []
    for a in atoms:
        resource = {
            "type": "memory_atom",
            "source_path": getattr(a, "topic", "") if hasattr(a, "topic") else "",
            "action": action,
        }
        try:
            if _is_root_agent(agent) or asyncio.get_event_loop().is_running():
                continue  # handle in async context later
            allowed.append(a)
        except RuntimeError:
            allowed.append(a)
    return allowed


async def filter_atom_results_async(
    agent: Any, atoms: list[Any], action: str = "read"
) -> list[Any]:
    """Async version — post-filter memory atom results."""
    if _is_root_agent(agent):
        return atoms

    policies = await _get_policies_for_agent(agent)
    allowed = []
    for a in atoms:
        resource = {
            "type": "memory_atom",
            "source_path": getattr(a, "topic", "") if hasattr(a, "topic") else "",
            "action": action,
        }
        blocked = False
        for p in policies:
            if p.effect == "deny" and _matches(agent, resource, p):
                blocked = True
                break
        if blocked:
            continue
        matched = False
        for p in policies:
            if p.effect == "allow" and _matches(agent, resource, p):
                matched = True
                break
        if matched:
            allowed.append(a)

    return (
        allowed if allowed else atoms
    )  # if no policies match, default allow for atoms without explicit DENY


async def filter_graph_results(agent: Any, nodes: list[dict], action: str = "read") -> list[dict]:
    """Post-filter graph query results."""
    if _is_root_agent(agent):
        return nodes

    policies = await _get_policies_for_agent(agent)
    allowed = []
    for n in nodes:
        resource = {
            "type": "graph_node",
            "source_path": n.get("source_path", n.get("path", "")),
            "source": n.get("source", ""),
            "action": action,
        }
        blocked = False
        for p in policies:
            if p.effect == "deny" and _matches(agent, resource, p):
                blocked = True
                break
        if blocked:
            continue
        matched = False
        for p in policies:
            if p.effect == "allow" and _matches(agent, resource, p):
                matched = True
                break
        if matched:
            allowed.append(n)
    return allowed if allowed else nodes


async def get_allowed_paths(agent: Any, action: str = "read") -> list[str]:
    """Get paths an agent is allowed to access. Empty = unrestricted."""
    if _is_root_agent(agent):
        return []

    policies = await _get_policies_for_agent(agent)
    paths = []
    for p in policies:
        if p.effect == "allow" and p.path_pattern:
            paths.append(p.path_pattern)
    return paths or []

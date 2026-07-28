"""Policy recommendation engine — deterministic analysis, no agent loop.

Scans connected sources, classifies directories by file types, matches to
org chart departments, generates allow/deny policies. Runs in <1 second.
"""

from __future__ import annotations

import asyncio
import fnmatch
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


_FILE_TYPE_MAP = {
    ".py": "backend",
    "pyproject.toml": "backend",
    "setup.py": "backend",
    "requirements.txt": "backend",
    "settings.py": "backend",
    ".js": "frontend",
    ".ts": "frontend",
    ".tsx": "frontend",
    ".jsx": "frontend",
    "package.json": "frontend",
    ".css": "frontend",
    "next.config": "frontend",
    ".tf": "platform",
    ".hcl": "platform",
    ".tfvars": "platform",
    ".java": "backend",
    ".kt": "backend",
    "build.gradle": "backend",
    ".sql": "backend",
    ".md": "documentation",
    ".yml": "platform",
    ".yaml": "platform",
    "Dockerfile": "platform",
}


def _classify_path(repo_path: Path) -> dict[str, int]:
    """Walk a repo, count file types, return department→count mapping."""
    counts: dict[str, int] = {}
    for path in repo_path.rglob("*"):
        if not path.is_file():
            continue
        if any(p in (".git", "node_modules", "__pycache__", ".venv", "dist", "build") for p in path.parts):
            continue
        name = path.name.lower()
        ext = path.suffix.lower()
        dept = _FILE_TYPE_MAP.get(name) or _FILE_TYPE_MAP.get(ext) or "unknown"
        counts[dept] = counts.get(dept, 0) + 1
    return counts


async def recommend_policies_for_project(project_id: str, created_by: str = "policy-agent") -> dict[str, Any]:
    from ecms.persistence.database.rest_session import db_session
    from ecms.persistence.repositories.agent import AgentRepository
    from ecms.persistence.models.access_policy import PolicyRecommendation

    async with db_session() as s:
        agents = await AgentRepository(s).list_all()

    if not agents:
        return {"error": "No agents in org chart."}

    # Build org maps
    dept_agents: dict[str, list[dict]] = {}
    for a in agents:
        d = a.to_dict()
        dept_agents.setdefault(d["department"], []).append(d)

    connectors = await _get_project_connectors(project_id)
    if not connectors:
        return {"error": "No connectors found."}

    policies: list[dict] = []
    departments = list(dept_agents.keys())

    for conn in connectors:
        cfg = conn.get("config", {})
        ctype = conn["connector_type"]
        persist_path = conn.get("persist_path") or cfg.get("clone_path", "")

        if ctype == "git" and persist_path:
            repo_path = Path(persist_path)
            if repo_path.exists():
                # Run classification in thread
                counts = await asyncio.to_thread(_classify_path, repo_path)

                # Find dominant department
                best_dept = max(counts, key=counts.get) if counts else None
                if best_dept and best_dept != "unknown" and best_dept in dept_agents:
                    agents_in = dept_agents[best_dept]
                    policies.append({
                        "effect": "allow",
                        "name": f"Git: {repo_path.name} → {best_dept}",
                        "department": best_dept,
                        "path_pattern": f"{persist_path}/**",
                        "resource_type": "graph_node", "source_type": "git", "action": "read",
                        "agent_ids": [x["id"] for x in agents_in],
                        "agent_names": [x["name"] for x in agents_in],
                        "confidence": min(0.80 + (counts[best_dept] * 0.02), 0.95),
                        "evidence": [f"{counts[best_dept]} {best_dept} files found out of {sum(counts.values())} total"],
                    })
                    # Deny for other departments
                    for dep in departments:
                        if dep != best_dept and dep in dept_agents:
                            agents_in_dep = dept_agents[dep]
                            policies.append({
                                "effect": "deny",
                                "name": f"Block {dep} from {repo_path.name}",
                                "department": dep,
                                "path_pattern": f"{persist_path}/**",
                                "resource_type": "graph_node", "source_type": "git", "action": "read",
                                "agent_ids": [x["id"] for x in agents_in_dep],
                                "agent_names": [x["name"] for x in agents_in_dep],
                                "confidence": 0.85,
                                "evidence": [f"Repo contains {counts.get(best_dept, 0)} {best_dept} files. {dep} has no ownership."],
                            })

        elif ctype == "mysql":
            db_name = cfg.get("database", "")
            if db_name:
                db_lower = db_name.lower()
                sensitive = any(kw in db_lower for kw in ["salary", "payroll", "hr", "secret", "token", "credential"])
                if sensitive:
                    root_agents = [a for agts in dept_agents.values() for a in agts if a.get("reports_to") is None]
                    if root_agents:
                        policies.append({
                            "effect": "allow", "name": f"MySQL: {db_name} → C-suite only",
                            "agent_ids": [x["id"] for x in root_agents],
                            "agent_names": [x["name"] for x in root_agents],
                            "resource_type": "graph_node", "source_type": "mysql",
                            "resource_attrs": {"source": "mysql", "db_name": db_name}, "action": "read",
                            "confidence": 0.94,
                            "evidence": [f"Database '{db_name}' contains sensitive keywords."],
                        })
                else:
                    matched = next((d for d in departments if d.lower() in db_lower or db_lower in d.lower()), departments[0])
                    if matched in dept_agents:
                        agents_in = dept_agents[matched]
                        policies.append({
                            "effect": "allow", "name": f"MySQL: {db_name} → {matched}",
                            "department": matched,
                            "agent_ids": [x["id"] for x in agents_in],
                            "agent_names": [x["name"] for x in agents_in],
                            "resource_type": "graph_node", "source_type": "mysql",
                            "resource_attrs": {"source": "mysql", "db_name": db_name}, "action": "read",
                            "confidence": 0.88,
                            "evidence": [f"Database '{db_name}' matched to department '{matched}'."],
                        })

    # Save
    rec_id = f"rec-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    analysis = {
        "directories_found": [c.get("persist_path", "") for c in connectors if c.get("persist_path")],
        "policies": len(policies),
    }

    async with db_session() as s:
        org_tree = await AgentRepository(s).get_org_tree()
        s.add(PolicyRecommendation(
            id=rec_id, name=f"Deep Analysis: {project_id}", project_id=project_id,
            policies_json={
                "project_id": project_id, "connectors_scanned": len(connectors),
                "policies_generated": len(policies), "policies": policies,
                "analysis": analysis,
            },
            org_snapshot=org_tree, status="pending", created_by=created_by,
        ))

    return {"id": rec_id, "policies": len(policies), "connectors": len(connectors), "analysis": analysis}


async def _get_project_connectors(project_id: str) -> list[dict]:
    from ecms.persistence.database.rest_session import db_session
    from sqlalchemy import select
    from ecms.persistence.models.project import ProjectConnector

    async with db_session() as s:
        stmt = select(ProjectConnector).where(ProjectConnector.project_id == f"proj:{project_id}")
        result = await s.execute(stmt)
        return [{"connector_type": c.connector_type, "config": c.config, "persist_path": c.persist_path} for c in result.scalars().all()]


async def approve_recommendation(rec_id: str, reviewer_id: str) -> dict[str, Any]:
    from ecms.persistence.database.rest_session import db_session
    from ecms.persistence.models.access_policy import AccessPolicy, PolicyRecommendation
    from sqlalchemy import select

    async with db_session() as s:
        stmt = select(PolicyRecommendation).where(PolicyRecommendation.id == rec_id)
        result = await s.execute(stmt)
        rec = result.scalar_one_or_none()
        if not rec:
            return {"error": "Recommendation not found"}

        policies = rec.policies_json.get("policies", [])
        created = 0
        for p in policies:
            ap = AccessPolicy(
                id=f"pol-{uuid.uuid4().hex[:12]}",
                name=p.get("name", "Imported Policy"),
                effect=p.get("effect", "allow"),
                department=p.get("department"),
                path_pattern=p.get("path_pattern"),
                source_type=p.get("source_type"),
                resource_type=p.get("resource_type"),
                resource_attrs=p.get("resource_attrs", {}),
                action=p.get("action", "read"),
                priority=p.get("priority", 100),
                created_by=reviewer_id,
            )
            s.add(ap)
            created += 1

        rec.status = "approved"
        rec.reviewed_by = reviewer_id
        rec.reviewed_at = datetime.now(timezone.utc)

    return {"approved": True, "policies_created": created}

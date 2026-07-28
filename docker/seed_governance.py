"""Backfill governance assignments for existing projects.

Run inside the Docker container:
  docker compose exec backend python seed_governance.py

For each project that has project agents but no governance assignments,
matches each project agent to the best-fitting org member by
department/role/skill overlap.
"""

import asyncio
import uuid
from ecms.persistence.database.rest_session import db_session
from sqlalchemy import text


def _normalize(s: str) -> str:
    return s.lower().replace("_", " ").replace("-", " ").strip()


def _score(agent_dept, agent_role, agent_skills, org_dept, org_role, org_skills):
    score = 0.0
    if agent_dept and org_dept:
        if agent_dept == org_dept:
            score += 0.5
        elif agent_dept in org_dept or org_dept in agent_dept:
            score += 0.3
    a_words = set(agent_role.split())
    o_words = set(org_role.split())
    common = a_words & o_words - {"the", "a", "an", "of", "and"}
    if common:
        score += 0.2 * min(1.0, len(common) / max(len(a_words), 1))
    if agent_skills and org_skills:
        overlap = agent_skills & org_skills
        if overlap:
            score += 0.3 * min(1.0, len(overlap) / max(len(agent_skills), 1))
    return score


async def main():
    async with db_session() as session:
        # Load org roster
        org_rows = (await session.execute(text(
            "SELECT id, name, role, department, skills FROM organization_members "
            "WHERE status = 'active'"
        ))).fetchall()
        org_roster = [
            {"id": r[0], "name": r[1], "role": r[2], "department": r[3],
             "skills": [s.lower() for s in (r[4] or [])]}
            for r in org_rows
        ]
        if not org_roster:
            print("No org members found.")
            return

        # Find projects with agents but no governance assignments
        project_ids = (await session.execute(text(
            "SELECT DISTINCT a.project_id FROM agents a "
            "WHERE a.project_id IS NOT NULL "
            "AND NOT EXISTS ("
            "  SELECT 1 FROM project_agent_governance_assignments g "
            "  WHERE g.project_id = a.project_id"
            ")"
        ))).fetchall()

        if not project_ids:
            print("All projects already have governance assignments.")
            return

        for (project_id,) in project_ids:
            agent_rows = (await session.execute(text(
                "SELECT id, name, role, department, skills FROM agents "
                "WHERE project_id = :pid AND status = 'active'"
            ), {"pid": project_id})).fetchall()

            agents = [
                {"id": r[0], "name": r[1], "role": r[2], "department": r[3],
                 "skills": [s.lower() for s in (r[4] or [])]}
                for r in agent_rows
            ]

            used = set()
            mappings = []
            for agent in agents:
                a_dept = _normalize(agent["department"])
                a_role = _normalize(agent["role"])
                a_skills = {_normalize(s) for s in agent["skills"]}

                best_score, best_member = -1.0, None
                for org in org_roster:
                    if org["id"] in used:
                        continue
                    o_dept = _normalize(org["department"])
                    o_role = _normalize(org["role"])
                    o_skills = {_normalize(s) for s in org["skills"]}
                    s = _score(a_dept, a_role, a_skills, o_dept, o_role, o_skills)
                    if s > best_score:
                        best_score, best_member = s, org

                if best_member:
                    used.add(best_member["id"])
                    mappings.append((agent["id"], best_member["id"], "primary_owner", best_score))

            # Assign remaining (if all org members used) to first org member
            assigned = {m[0] for m in mappings}
            for agent in agents:
                if agent["id"] not in assigned:
                    mappings.append((agent["id"], org_roster[0]["id"], "monitor", 0.0))

            for agent_id, org_id, resp, _ in mappings:
                await session.execute(text(
                    "INSERT INTO project_agent_governance_assignments "
                    "(id, organization_member_id, project_agent_id, project_id, "
                    "responsibility, status, assigned_by_user_id, assigned_at, updated_at) "
                    "VALUES (:id, :mid, :aid, :pid, :resp, 'active', 'ba_agent', NOW(), NOW())"
                ), {
                    "id": f"gov-{uuid.uuid4().hex[:12]}",
                    "mid": org_id,
                    "aid": agent_id,
                    "pid": project_id,
                    "resp": resp,
                })

            await session.commit()
            print(f"Seeded {len(mappings)} governance assignments for project {project_id}")
            for agent_id, org_id, resp, score in mappings:
                agent_name = next((a["name"] for a in agents if a["id"] == agent_id), agent_id)
                org_name = next((o["name"] for o in org_roster if o["id"] == org_id), org_id)
                print(f"  {agent_name} → {org_name} ({resp}, score={score:.2f})")


if __name__ == "__main__":
    asyncio.run(main())

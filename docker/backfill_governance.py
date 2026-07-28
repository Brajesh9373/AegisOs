"""Backfill governance assignments for existing projects using organization_members."""
import asyncio, uuid
from ecms.persistence.database.rest_session import db_session
from sqlalchemy import text

def _normalize(s):
    return s.lower().replace("_", " ").replace("-", " ").strip()

def _score(a_dept, a_role, a_skills, o_dept, o_role, o_skills):
    score = 0.0
    if a_dept and o_dept:
        if a_dept == o_dept:
            score += 0.5
        elif a_dept in o_dept or o_dept in a_dept:
            score += 0.3
    a_words = set(a_role.split())
    o_words = set(o_role.split())
    common = a_words & o_words - {"the", "a", "an", "of", "and"}
    if common:
        score += 0.2 * min(1.0, len(common) / max(len(a_words), 1))
    if a_skills and o_skills:
        overlap = a_skills & o_skills
        if overlap:
            score += 0.3 * min(1.0, len(overlap) / max(len(a_skills), 1))
    return score

async def main():
    async with db_session() as session:
        org_rows = (await session.execute(text(
            "SELECT id, name, role, department, skills FROM organization_members WHERE status = 'active'"
        ))).fetchall()
        org_roster = [
            {"id": r[0], "name": r[1], "role": r[2], "department": r[3],
             "skills": [s.lower() for s in (r[4] or [])]}
            for r in org_rows
        ]
        print(f"Org roster: {len(org_roster)} members")

        project_ids = (await session.execute(text(
            "SELECT DISTINCT a.project_id FROM agents a "
            "WHERE a.project_id IS NOT NULL "
            "AND NOT EXISTS (SELECT 1 FROM project_agent_governance_assignments g WHERE g.project_id = a.project_id)"
        ))).fetchall()
        print(f"Projects needing governance: {len(project_ids)}")

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
            print(f"Created {len(mappings)} governance assignments for project {project_id}")
            for agent_id, org_id, resp, score in mappings:
                a_name = next((a["name"] for a in agents if a["id"] == agent_id), agent_id)
                o_name = next((o["name"] for o in org_roster if o["id"] == org_id), org_id)
                print(f"  {a_name} -> {o_name} ({resp}, score={score:.2f})")

if __name__ == "__main__":
    asyncio.run(main())

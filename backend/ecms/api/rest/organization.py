"""Organization member REST API.

Endpoints for managing the permanent AegisOS company hierarchy.
These are distinct from project-scoped runtime agents.
"""

from __future__ import annotations

import uuid as _uuid

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ecms.persistence.database.rest_session import db_session
from ecms.persistence.repositories.organization_member import OrganizationMemberRepository

router = APIRouter(prefix="/organization/members", tags=["organization"])
tool_router = APIRouter(prefix="/organization/tool-assignments", tags=["org-tool-assignments"])


class CreateMemberRequest(BaseModel):
    id: str
    name: str
    designation: str = ""
    role: str
    department: str
    role_description: str | None = None
    skills: list | None = None
    reports_to: str | None = None
    status: str = "active"
    user_id: str | None = None


class UpdateMemberRequest(BaseModel):
    name: str | None = None
    designation: str | None = None
    role: str | None = None
    department: str | None = None
    role_description: str | None = None
    skills: list | None = None
    reports_to: str | None = None
    status: str | None = None
    user_id: str | None = None


@router.get("")
async def list_members():
    """List all organization members (permanent hierarchy only)."""
    async with db_session() as s:
        repo = OrganizationMemberRepository(s)
        members = await repo.list_all()
        return [m.to_dict() for m in members]


@router.get("/tree")
async def org_tree():
    """Return the org hierarchy as a nested tree."""
    async with db_session() as s:
        repo = OrganizationMemberRepository(s)
        return await repo.get_org_tree()


@router.get("/{member_id}")
async def get_member(member_id: str):
    """Get a single member with their direct reports."""
    async with db_session() as s:
        repo = OrganizationMemberRepository(s)
        member = await repo.get(member_id)
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")
        data = member.to_dict()
        reports = await repo.list_by_manager(member_id)
        data["reports"] = [r.to_dict() for r in reports]
        # Include assignment summary counts
        from ecms.persistence.repositories.governance_assignment import (
            GovernanceAssignmentRepository,
        )

        gov_repo = GovernanceAssignmentRepository(s)
        assignments = await gov_repo.list_by_member(member_id)
        data["assignment_counts"] = {
            "total": len(assignments),
            "active": sum(1 for a in assignments if a.status == "active"),
            "needs_review": sum(1 for a in assignments if a.status == "needs_review"),
        }
        return data


@router.post("")
async def create_member(body: CreateMemberRequest):
    """Create a new organization member."""
    async with db_session() as s:
        repo = OrganizationMemberRepository(s)
        existing = await repo.get(body.id)
        if existing:
            raise HTTPException(status_code=409, detail="Member ID already exists")
        # Validate reports_to exists if provided
        if body.reports_to:
            manager = await repo.get(body.reports_to)
            if not manager:
                raise HTTPException(status_code=400, detail="Manager not found")
            if body.reports_to == body.id:
                raise HTTPException(status_code=400, detail="Member cannot report to itself")
        kwargs = body.model_dump()
        member = await repo.create(**kwargs)
        return member.to_dict()


@router.put("/{member_id}")
async def update_member(member_id: str, body: UpdateMemberRequest):
    """Update an organization member."""
    async with db_session() as s:
        repo = OrganizationMemberRepository(s)
        member = await repo.get(member_id)
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")
        kwargs = {k: v for k, v in body.model_dump().items() if v is not None}
        # Validate reports_to cycle if being changed
        if kwargs.get("reports_to"):
            if kwargs["reports_to"] == member_id:
                raise HTTPException(status_code=400, detail="Member cannot report to itself")
            if await repo.is_in_reporting_chain(member_id, kwargs["reports_to"]):
                raise HTTPException(status_code=400, detail="Reporting cycle detected")
        updated = await repo.update(member_id, **kwargs)
        return updated.to_dict()


@router.post("/{member_id}/deactivate")
async def deactivate_member(member_id: str):
    """Deactivate an organization member."""
    async with db_session() as s:
        repo = OrganizationMemberRepository(s)
        member = await repo.get(member_id)
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")
        if member.status == "inactive":
            raise HTTPException(status_code=400, detail="Member is already inactive")
        await repo.deactivate(member_id)
        return {"deactivated": True, "member_id": member_id}


@router.delete("/{member_id}")
async def delete_member(member_id: str):
    """Delete an organization member. Blocked if reports or assignments exist."""
    async with db_session() as s:
        repo = OrganizationMemberRepository(s)
        member = await repo.get(member_id)
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")
        # Check for direct reports
        reports = await repo.list_by_manager(member_id)
        if reports:
            raise HTTPException(
                status_code=409,
                detail=f"Cannot delete: member has {len(reports)} direct reports. Deactivate instead.",
            )
        # Check for active governance assignments
        from ecms.persistence.repositories.governance_assignment import (
            GovernanceAssignmentRepository,
        )

        gov_repo = GovernanceAssignmentRepository(s)
        if await gov_repo.has_active_assignments(member_id):
            raise HTTPException(
                status_code=409,
                detail="Cannot delete: member has active governance assignments. Revoke them first.",
            )
        deleted = await repo.delete(member_id)
        return {"deleted": True, "member_id": member_id}


# ---------------------------------------------------------------------------
# Seed endpoint: populate the default AegisOS org hierarchy
# ---------------------------------------------------------------------------

# Full 28-person software company hierarchy
_SEED_ORG: list[dict] = [
    {
        "id": "org-ceo",
        "name": "Vikram Sharma",
        "role": "ceo",
        "designation": "Chief Executive Officer",
        "department": "leadership",
        "reports_to": None,
        "role_description": "Sets company vision, leads fundraising, manages key client relationships and board reporting.",
        "skills": ["Strategy", "Fundraising", "Client Relations", "Product Vision"],
    },
    {
        "id": "org-cto",
        "name": "Priya Mehta",
        "role": "cto",
        "designation": "Chief Technology Officer",
        "department": "leadership",
        "reports_to": "org-ceo",
        "role_description": "Owns technical architecture, engineering hiring, technology roadmap, and platform reliability.",
        "skills": ["Architecture", "Python", "Cloud", "System Design"],
    },
    {
        "id": "org-cpo",
        "name": "Aditya Bose",
        "role": "cpo",
        "designation": "Chief Product Officer",
        "department": "leadership",
        "reports_to": "org-ceo",
        "role_description": "Owns product strategy, discovery, design, positioning, and the product roadmap.",
        "skills": ["Product Strategy", "Market Research", "Roadmapping", "Product-Led Growth"],
    },
    {
        "id": "org-coo",
        "name": "Leena Krishnan",
        "role": "coo",
        "designation": "Chief Operating Officer",
        "department": "leadership",
        "reports_to": "org-ceo",
        "role_description": "Runs company operations, delivery governance, customer success, and organizational planning.",
        "skills": ["Operations", "Delivery Governance", "Capacity Planning", "Customer Success"],
    },
    {
        "id": "org-cfo",
        "name": "Arjun Nair",
        "role": "cfo",
        "designation": "Chief Financial Officer",
        "department": "leadership",
        "reports_to": "org-ceo",
        "role_description": "Manages budgets, vendor negotiations, resource allocation, and financial strategy.",
        "skills": ["Finance", "Budgeting", "Compliance", "Investor Relations"],
    },
    {
        "id": "org-dir-eng",
        "name": "Siddharth Mehta",
        "role": "director_engineering",
        "designation": "Director of Engineering",
        "department": "engineering",
        "reports_to": "org-cto",
        "role_description": "Manages all engineering pods. Owns delivery velocity, technical standards, cross-team coordination, and engineering culture.",
        "skills": ["Engineering Management", "Delivery", "Architecture Reviews", "Hiring"],
    },
    {
        "id": "org-lead-backend",
        "name": "Karan Malhotra",
        "role": "engineering_manager",
        "designation": "Backend Manager",
        "department": "backend",
        "reports_to": "org-dir-eng",
        "role_description": "Leads backend team. Designs APIs, database schema, and owns service reliability.",
        "skills": ["Python", "FastAPI", "PostgreSQL", "Redis", "Microservices"],
    },
    {
        "id": "org-sr-backend-1",
        "name": "Divya Singh",
        "role": "senior_dev",
        "designation": "Senior Backend Engineer",
        "department": "backend",
        "reports_to": "org-lead-backend",
        "role_description": "Builds core platform services, authentication flows, and third-party integrations.",
        "skills": ["Python", "SQLAlchemy", "JWT", "OAuth2"],
    },
    {
        "id": "org-sr-backend-2",
        "name": "Rajesh Kumar",
        "role": "senior_dev",
        "designation": "Senior Backend Engineer",
        "department": "backend",
        "reports_to": "org-lead-backend",
        "role_description": "Owns search infrastructure, background jobs, and event-driven architecture.",
        "skills": ["Python", "Kafka", "Elasticsearch", "Celery"],
    },
    {
        "id": "org-mid-backend",
        "name": "Ananya Iyer",
        "role": "mid_dev",
        "designation": "Backend Engineer",
        "department": "backend",
        "reports_to": "org-lead-backend",
        "role_description": "Develops REST endpoints, writes integration tests, and maintains API documentation.",
        "skills": ["FastAPI", "pytest", "PostgreSQL", "OpenAPI"],
    },
    {
        "id": "org-jr-backend",
        "name": "Vikram Patil",
        "role": "junior_dev",
        "designation": "Junior Backend Engineer",
        "department": "backend",
        "reports_to": "org-sr-backend-1",
        "role_description": "Builds CRUD endpoints, writes unit tests, and resolves backlog bugs.",
        "skills": ["Python", "FastAPI", "SQL", "Git"],
    },
    {
        "id": "org-lead-frontend",
        "name": "Kunal Shah",
        "role": "engineering_manager",
        "designation": "Frontend Manager",
        "department": "frontend",
        "reports_to": "org-dir-eng",
        "role_description": "Leads frontend architecture, component library, and performance optimization.",
        "skills": ["React", "TypeScript", "Next.js", "Design Systems"],
    },
    {
        "id": "org-sr-frontend-1",
        "name": "Pooja Verma",
        "role": "senior_dev",
        "designation": "Senior Frontend Engineer",
        "department": "frontend",
        "reports_to": "org-lead-frontend",
        "role_description": "Builds complex dashboards, real-time collaboration UI, and state management.",
        "skills": ["React", "Zustand", "WebSocket", "D3.js"],
    },
    {
        "id": "org-sr-frontend-2",
        "name": "Meera Choudhury",
        "role": "senior_dev",
        "designation": "Senior Frontend Engineer",
        "department": "frontend",
        "reports_to": "org-lead-frontend",
        "role_description": "Owns responsive layouts, accessibility compliance, and cross-browser testing.",
        "skills": ["React", "Tailwind CSS", "a11y", "Playwright"],
    },
    {
        "id": "org-mid-frontend",
        "name": "Aakash Tiwari",
        "role": "mid_dev",
        "designation": "Frontend Engineer",
        "department": "frontend",
        "reports_to": "org-lead-frontend",
        "role_description": "Implements UI features from specs, writes component tests, and handles design handoffs.",
        "skills": ["React", "TypeScript", "CSS", "Jest"],
    },
    {
        "id": "org-platform-mgr",
        "name": "Rohan Gupta",
        "role": "engineering_manager",
        "designation": "Platform Manager",
        "department": "platform",
        "reports_to": "org-dir-eng",
        "role_description": "Manages cloud infrastructure, developer experience, and internal platform tooling.",
        "skills": ["Docker", "Kubernetes", "Terraform", "AWS", "GitHub Actions"],
    },
    {
        "id": "org-devops-mgr",
        "name": "Sneha Kapoor",
        "role": "engineering_manager",
        "designation": "DevOps Manager",
        "department": "devops",
        "reports_to": "org-dir-eng",
        "role_description": "Owns CI/CD pipelines, deployment automation, monitoring, and production reliability.",
        "skills": ["CI/CD", "Helm", "Prometheus", "Grafana", "ArgoCD"],
    },
    {
        "id": "org-qa-mgr",
        "name": "Ravi Menon",
        "role": "quality_engineering_manager",
        "designation": "QA Manager",
        "department": "qa",
        "reports_to": "org-dir-eng",
        "role_description": "Owns test strategy, automation framework, and release quality sign-off.",
        "skills": ["Cypress", "Playwright", "pytest", "CI/CD", "Test Strategy"],
    },
    {
        "id": "org-qa",
        "name": "Swati Das",
        "role": "mid_dev",
        "designation": "QA Engineer",
        "department": "qa",
        "reports_to": "org-qa-mgr",
        "role_description": "Writes test cases, automates regression suites, and tracks defect metrics.",
        "skills": ["Selenium", "Postman", "Bug Tracking", "Test Cases"],
    },
    {
        "id": "org-data-lead",
        "name": "Sanjay Rao",
        "role": "tech_lead",
        "designation": "Data Lead",
        "department": "data",
        "reports_to": "org-dir-eng",
        "role_description": "Leads data engineering. Builds ETL pipelines, manages analytics warehouse, and creates dashboards.",
        "skills": ["Python", "SQL", "Airflow", "dbt", "Metabase"],
    },
    {
        "id": "org-fullstack",
        "name": "Amit Joshi",
        "role": "mid_dev",
        "designation": "Full-Stack Engineer",
        "department": "engineering",
        "reports_to": "org-platform-mgr",
        "role_description": "Works across backend and frontend. Builds features end-to-end and handles cross-cutting concerns.",
        "skills": ["React", "Python", "FastAPI", "PostgreSQL", "TypeScript"],
    },
    {
        "id": "org-security",
        "name": "Harsh Vardhan",
        "role": "security_lead",
        "designation": "Head of Security",
        "department": "security",
        "reports_to": "org-cto",
        "role_description": "Owns application security, privacy controls, threat management, and compliance readiness.",
        "skills": ["Security Architecture", "Threat Modeling", "ISO 27001", "AppSec"],
    },
    {
        "id": "org-pm",
        "name": "Nisha Kulkarni",
        "role": "product_manager",
        "designation": "Product Manager",
        "department": "product",
        "reports_to": "org-cpo",
        "role_description": "Owns product roadmap, user research, feature prioritization, and release planning.",
        "skills": ["Product Discovery", "User Research", "Agile", "Analytics"],
    },
    {
        "id": "org-designer",
        "name": "Rhea Sen",
        "role": "product_designer",
        "designation": "Product Designer",
        "department": "design",
        "reports_to": "org-cpo",
        "role_description": "Designs user workflows, maintains the design system, and validates usability through testing.",
        "skills": ["Figma", "UX Design", "Prototyping", "Design Systems"],
    },
    {
        "id": "org-cs",
        "name": "Anjali Desai",
        "role": "customer_success_head",
        "designation": "Head of Customer Success",
        "department": "customer_success",
        "reports_to": "org-coo",
        "role_description": "Manages client onboarding, support escalations, adoption, and renewal health.",
        "skills": ["Customer Success", "Onboarding", "Communication", "CRM"],
    },
    {
        "id": "org-program-mgr",
        "name": "Aparna Nandakumar",
        "role": "program_manager",
        "designation": "Program Manager",
        "department": "delivery_operations",
        "reports_to": "org-coo",
        "role_description": "Coordinates strategic programs, dependencies, risks, and executive reporting.",
        "skills": ["Program Management", "Risk Management", "Planning", "Executive Reporting"],
    },
    {
        "id": "org-people",
        "name": "Kavya Rao",
        "role": "people_operations_head",
        "designation": "Head of People Operations",
        "department": "people_operations",
        "reports_to": "org-coo",
        "role_description": "Owns talent systems, performance, culture, learning, and employee experience.",
        "skills": ["People Strategy", "Performance", "Culture", "Learning"],
    },
    {
        "id": "org-controller",
        "name": "Shreya Mukherjee",
        "role": "financial_controller",
        "designation": "Financial Controller",
        "department": "finance",
        "reports_to": "org-cfo",
        "role_description": "Owns financial controls, reporting, planning cycles, and operational accounting.",
        "skills": ["Financial Controls", "FP&A", "Accounting", "Reporting"],
    },
    {
        "id": "org-finance-analyst",
        "name": "Naveen Pillai",
        "role": "finance_analyst",
        "designation": "Finance Analyst",
        "department": "finance",
        "reports_to": "org-controller",
        "role_description": "Builds forecasts, unit economics, management reporting, and investment analysis.",
        "skills": ["Forecasting", "Unit Economics", "Excel", "Financial Modeling"],
    },
]


@router.post("/seed")
async def seed_organization():
    """Seed the default AegisOS organization hierarchy.

    Idempotent: skips members that already exist.
    Also auto-seeds tool assignments based on department/role.
    """
    created = 0
    skipped = 0
    async with db_session() as s:
        repo = OrganizationMemberRepository(s)
        for m in _SEED_ORG:
            existing = await repo.get(m["id"])
            if existing:
                skipped += 1
                continue
            await repo.create(**m)
            created += 1

    # Auto-seed tool assignments if we created new members
    tools_created = 0
    if created > 0:
        async with db_session() as s:
            from sqlalchemy import text

            members = (
                await s.execute(
                    text("SELECT id, department FROM organization_members WHERE status = 'active'")
                )
            ).fetchall()
            for member_id, dept in members:
                tools = _ROLE_TOOL_MAP.get(dept, [])
                for tool in tools:
                    aid = f"ta-{_uuid.uuid4().hex[:12]}"
                    try:
                        await s.execute(
                            text(
                                "INSERT INTO org_tool_assignments (id, organization_member_id, tool_name, assigned_at) "
                                "VALUES (:id, :mid, :tn, NOW()) ON CONFLICT (organization_member_id, tool_name) DO NOTHING"
                            ),
                            {"id": aid, "mid": member_id, "tn": tool},
                        )
                        tools_created += 1
                    except Exception:
                        pass
            await s.commit()

    return {
        "created": created,
        "skipped": skipped,
        "total": len(_SEED_ORG),
        "tools_assigned": tools_created,
    }


# ---------------------------------------------------------------------------
# Tool-to-Org-Member assignment endpoints
# ---------------------------------------------------------------------------

# Role/department → tool mapping for auto-assignment
_ROLE_TOOL_MAP: dict[str, list[str]] = {
    "leadership": ["Jira", "Slack"],
    "backend": ["GitHub", "Git", "Jira"],
    "frontend": ["GitHub", "Git", "Jira"],
    "engineering": ["GitHub", "Git", "Jira"],
    "devops": ["AWS", "GCP", "Azure", "GitHub", "Git", "GitLab"],
    "platform": ["AWS", "GCP", "Azure", "GitHub", "Git", "GitLab"],
    "qa": ["Jira", "Git", "GitHub"],
    "security": ["GitHub", "Git"],
    "data": ["GCP", "Git"],
    "product": ["Jira", "Asana", "Slack"],
    "design": ["Jira", "Asana", "Slack"],
    "delivery_operations": ["Jira", "Asana", "Slack", "Teams"],
    "customer_success": ["Slack", "Teams", "Meet"],
    "people_operations": ["Slack", "Teams"],
    "finance": ["Asana"],
}


@tool_router.get("")
async def list_tool_assignments(tool_name: str | None = Query(None)):
    """List all tool-to-org-member assignments, optionally filtered by tool."""
    async with db_session() as s:
        from sqlalchemy import text

        if tool_name:
            rows = (
                await s.execute(
                    text(
                        "SELECT id, organization_member_id, tool_name, assigned_at "
                        "FROM org_tool_assignments WHERE tool_name = :tn ORDER BY tool_name"
                    ),
                    {"tn": tool_name},
                )
            ).fetchall()
        else:
            rows = (
                await s.execute(
                    text(
                        "SELECT id, organization_member_id, tool_name, assigned_at "
                        "FROM org_tool_assignments ORDER BY tool_name"
                    )
                )
            ).fetchall()
        return [
            {
                "id": r[0],
                "organization_member_id": r[1],
                "tool_name": r[2],
                "assigned_at": str(r[3]),
            }
            for r in rows
        ]


class ToolAssignmentRequest(BaseModel):
    organization_member_id: str
    tool_name: str


@tool_router.post("")
async def create_tool_assignment(body: ToolAssignmentRequest):
    """Manually assign a tool to an org member."""
    async with db_session() as s:
        from sqlalchemy import text

        # Validate member exists
        member = (
            await s.execute(
                text("SELECT id FROM organization_members WHERE id = :id"),
                {"id": body.organization_member_id},
            )
        ).first()
        if not member:
            raise HTTPException(status_code=404, detail="Organization member not found")
        # Check duplicate
        existing = (
            await s.execute(
                text(
                    "SELECT id FROM org_tool_assignments WHERE organization_member_id = :mid AND tool_name = :tn"
                ),
                {"mid": body.organization_member_id, "tn": body.tool_name},
            )
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="Tool already assigned to this member")
        aid = f"ta-{_uuid.uuid4().hex[:12]}"
        await s.execute(
            text(
                "INSERT INTO org_tool_assignments (id, organization_member_id, tool_name, assigned_at) "
                "VALUES (:id, :mid, :tn, NOW())"
            ),
            {"id": aid, "mid": body.organization_member_id, "tn": body.tool_name},
        )
        await s.commit()
        return {
            "id": aid,
            "organization_member_id": body.organization_member_id,
            "tool_name": body.tool_name,
        }


@tool_router.delete("/{assignment_id}")
async def delete_tool_assignment(assignment_id: str):
    """Remove a tool assignment."""
    async with db_session() as s:
        from sqlalchemy import text

        result = await s.execute(
            text("DELETE FROM org_tool_assignments WHERE id = :id"), {"id": assignment_id}
        )
        await s.commit()
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Assignment not found")
        return {"deleted": True, "id": assignment_id}


@tool_router.post("/auto-seed")
async def auto_seed_tool_assignments():
    """Auto-assign tools to org members based on department/role.

    Idempotent: skips assignments that already exist.
    """
    async with db_session() as s:
        from sqlalchemy import text

        members = (
            await s.execute(
                text("SELECT id, department FROM organization_members WHERE status = 'active'")
            )
        ).fetchall()

        created = 0
        skipped = 0
        for member_id, dept in members:
            tools = _ROLE_TOOL_MAP.get(dept, [])
            for tool in tools:
                aid = f"ta-{_uuid.uuid4().hex[:12]}"
                try:
                    await s.execute(
                        text(
                            "INSERT INTO org_tool_assignments (id, organization_member_id, tool_name, assigned_at) "
                            "VALUES (:id, :mid, :tn, NOW()) ON CONFLICT (organization_member_id, tool_name) DO NOTHING"
                        ),
                        {"id": aid, "mid": member_id, "tn": tool},
                    )
                    created += 1
                except Exception:
                    skipped += 1
        await s.commit()
        return {"created": created, "skipped": skipped}

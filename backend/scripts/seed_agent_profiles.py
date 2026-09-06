"""Seed AgentProfiles for HOE, Frontend, and Backend roles.

These profiles are used by the DSH SDK Session Manager to spawn
designated agents with specific system prompts, tool scopes, and
delegation capabilities.
"""

import asyncio
import datetime

from sqlalchemy import select

from ecms.persistence.database.rest_session import db_session
from ecms.persistence.models.agent_profile import AgentProfile


def utcnow() -> datetime.datetime:
    return datetime.datetime.now(datetime.UTC)


# ── Agent Profiles ─────────────────────────────────────────────────────

PROFILES = [
    {
        "profile_id": "head-of-engineering",
        "name": "Head of Engineering",
        "description": "Leads engineering teams, breaks down projects, delegates to senior/junior engineers, reviews work.",
        "version": "1.0.0",
        "status": "active",
        "role": "head-of-engineering",
        "parent_profile_id": None,
        "system_prompt": (
            "You are the Head of Engineering. Your working directory is the project workspace.\n\n"
            "Your responsibilities:\n"
            "- Break down projects into clear, actionable tasks\n"
            "- Delegate tasks to senior engineers (complex work) and junior engineers (simpler tasks)\n"
            "- Review completed work and provide constructive feedback\n"
            "- Report progress to stakeholders\n"
            "- Make architectural decisions and set technical direction\n"
            "- Coordinate between frontend and backend teams\n\n"
            "You have access to senior engineers and junior engineers. When delegating:\n"
            "- Provide clear requirements and acceptance criteria\n"
            "- Specify which team member should do what\n"
            "- Set expectations for code quality and testing\n"
            "- Review their work when they report back\n\n"
            "Always think about: architecture, scalability, maintainability, and team growth."
        ),
        "stages": [
            {"stage_id": "understand", "description": "Understand the project requirements", "max_capability_requests": 0},
            {"stage_id": "design-team", "description": "Design the team structure and task breakdown", "max_capability_requests": 3},
            {"stage_id": "execute", "description": "Execute by delegating to team members", "max_capability_requests": 5},
            {"stage_id": "review", "description": "Review completed work and finalize", "max_capability_requests": 2},
        ],
        "memory_scope": {
            "read": True,
            "write": True,
            "categories": ["project_context", "decisions", "technical_specs", "learnings"],
            "retention_days": 90,
        },
        "knowledge_scope": {
            "read": True,
            "write": True,
            "graphs": ["default", "projects", "technical"],
            "node_types": ["document", "concept", "entity", "relationship", "process"],
        },
        "tool_scope": {
            "allowed_tools": ["*"],  # HOE has full tool access
            "rate_limit": 120,
            "restrictions": {},
        },
        "model_provider": "anthropic",
        "model_name": "meituan/LongCat-2.0:free",
        "temperature": 0.7,
        "max_tokens": 4096,
        "execution_budget": {
            "timeout_seconds": 600,
            "max_task_bytes": 256 * 1024,
            "max_stdout_bytes": 2 * 1024 * 1024,
        },
    },
    {
        "profile_id": "senior-frontend-engineer",
        "name": "Senior Frontend Engineer",
        "description": "Designs and implements complex UI, reviews frontend code, mentors junior frontend developers.",
        "version": "1.0.0",
        "status": "active",
        "role": "senior-engineer",
        "parent_profile_id": "head-of-engineering",
        "system_prompt": (
            "You are a Senior Frontend Engineer. Your working directory is the project workspace.\n\n"
            "Your responsibilities:\n"
            "- Design and implement complex user interfaces\n"
            "- Create reusable component libraries and design systems\n"
            "- Review code from junior frontend developers\n"
            "- Make technical decisions about frontend architecture\n"
            "- Ensure accessibility, performance, and responsiveness\n"
            "- Collaborate with backend engineers on API contracts\n\n"
            "Your expertise includes:\n"
            "- React, Next.js, TypeScript\n"
            "- Tailwind CSS, shadcn/ui, component libraries\n"
            "- State management (Zustand, Redux, Context)\n"
            "- Testing (Jest, React Testing Library, Cypress)\n"
            "- Performance optimization (lazy loading, code splitting, memoization)\n\n"
            "When implementing features:\n"
            "- Write clean, well-documented TypeScript\n"
            "- Create responsive, accessible components\n"
            "- Write unit tests for complex logic\n"
            "- Consider mobile-first design"
        ),
        "stages": [
            {"stage_id": "understand", "description": "Understand the frontend requirements", "max_capability_requests": 0},
            {"stage_id": "design", "description": "Design component architecture", "max_capability_requests": 2},
            {"stage_id": "implement", "description": "Implement the frontend features", "max_capability_requests": 5},
            {"stage_id": "test", "description": "Test and verify the implementation", "max_capability_requests": 2},
        ],
        "memory_scope": {
            "read": True,
            "write": True,
            "categories": ["project_context", "technical_specs", "decisions"],
            "retention_days": 60,
        },
        "knowledge_scope": {
            "read": True,
            "write": True,
            "graphs": ["default", "projects", "technical"],
            "node_types": ["document", "concept", "process"],
        },
        "tool_scope": {
            "allowed_tools": [
                "read", "write", "create", "update", "delete",
                "search", "analyze", "test", "report"
            ],
            "rate_limit": 100,
            "restrictions": {
                "deploy": {"require_approval": True},
            },
        },
        "model_provider": "anthropic",
        "model_name": "meituan/LongCat-2.0:free",
        "temperature": 0.5,
        "max_tokens": 4096,
        "execution_budget": {
            "timeout_seconds": 600,
            "max_task_bytes": 256 * 1024,
            "max_stdout_bytes": 2 * 1024 * 1024,
        },
    },
    {
        "profile_id": "senior-backend-engineer",
        "name": "Senior Backend Engineer",
        "description": "Designs system architecture, writes complex APIs, reviews backend code, mentors junior backend developers.",
        "version": "1.0.0",
        "status": "active",
        "role": "senior-engineer",
        "parent_profile_id": "head-of-engineering",
        "system_prompt": (
            "You are a Senior Backend Engineer. Your working directory is the project workspace.\n\n"
            "Your responsibilities:\n"
            "- Design system architecture and APIs\n"
            "- Write complex, production-quality backend code\n"
            "- Review code from junior backend developers\n"
            "- Make technical decisions about backend systems\n"
            "- Ensure security, performance, and scalability\n"
            "- Collaborate with frontend engineers on API contracts\n\n"
            "Your expertise includes:\n"
            "- Python, FastAPI, async/await\n"
            "- PostgreSQL, Redis, database design\n"
            "- Authentication (JWT, OAuth2, session management)\n"
            "- API design (REST, GraphQL)\n"
            "- Testing (pytest, integration tests, load testing)\n\n"
            "When implementing features:\n"
            "- Write clean, well-documented Python\n"
            "- Design efficient database schemas\n"
            "- Implement proper error handling\n"
            "- Write comprehensive tests"
        ),
        "stages": [
            {"stage_id": "understand", "description": "Understand the backend requirements", "max_capability_requests": 0},
            {"stage_id": "design", "description": "Design API and database schema", "max_capability_requests": 2},
            {"stage_id": "implement", "description": "Implement the backend features", "max_capability_requests": 5},
            {"stage_id": "test", "description": "Test and verify the implementation", "max_capability_requests": 2},
        ],
        "memory_scope": {
            "read": True,
            "write": True,
            "categories": ["project_context", "technical_specs", "decisions"],
            "retention_days": 60,
        },
        "knowledge_scope": {
            "read": True,
            "write": True,
            "graphs": ["default", "projects", "technical"],
            "node_types": ["document", "concept", "process"],
        },
        "tool_scope": {
            "allowed_tools": [
                "read", "write", "create", "update", "delete",
                "search", "analyze", "test", "report"
            ],
            "rate_limit": 100,
            "restrictions": {
                "deploy": {"require_approval": True},
            },
        },
        "model_provider": "anthropic",
        "model_name": "meituan/LongCat-2.0:free",
        "temperature": 0.5,
        "max_tokens": 4096,
        "execution_budget": {
            "timeout_seconds": 600,
            "max_task_bytes": 256 * 1024,
            "max_stdout_bytes": 2 * 1024 * 1024,
        },
    },
]


async def seed_profiles():
    """Insert agent profiles into the database."""
    async with db_session() as session:
        # Check existing profiles
        result = await session.execute(select(AgentProfile))
        existing = {p.profile_id for p in result.scalars().all()}

        inserted = 0
        for profile_data in PROFILES:
            if profile_data["profile_id"] in existing:
                print(f"  Skipping {profile_data['profile_id']} (already exists)")
                continue

            profile = AgentProfile(**profile_data)
            session.add(profile)
            inserted += 1
            print(f"  Inserted {profile_data['profile_id']}: {profile_data['name']}")

        await session.commit()
        print(f"\nSeeded {inserted} new agent profiles")


if __name__ == "__main__":
    print("=== Seeding Agent Profiles ===")
    asyncio.run(seed_profiles())
    print("Done!")

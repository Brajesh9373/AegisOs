"""Platform tables: organization, users, auth_sessions, business_projects,
project_agents, execution_nodes, human_queue.

Revision ID: 0013
Revises: 0012
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0013_platform_tables"
down_revision: str | None = "0012_categories"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. organization — singleton org install config
    op.execute("""
        CREATE TABLE IF NOT EXISTS organization (
            id              TEXT PRIMARY KEY,
            name            TEXT NOT NULL,
            domain          TEXT NOT NULL,
            setupComplete   INTEGER NOT NULL DEFAULT 0,
            licenseKey      TEXT,
            aiProvider      TEXT,
            aiApiKey        TEXT,
            aiModel         TEXT,
            storage         TEXT,
            database        TEXT
        )
    """)

    # 2. users — platform users/employees
    op.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id              TEXT PRIMARY KEY,
            email           TEXT UNIQUE NOT NULL,
            passwordHash    TEXT NOT NULL,
            role            TEXT NOT NULL,
            department      TEXT,
            active          INTEGER NOT NULL DEFAULT 1
        )
    """)

    # 3. auth_sessions — auth token store (renamed from 'sessions' to avoid conflict)
    op.execute("""
        CREATE TABLE IF NOT EXISTS auth_sessions (
            id              TEXT PRIMARY KEY,
            userId          TEXT NOT NULL,
            token           TEXT NOT NULL,
            expiresAt       TEXT NOT NULL
        )
    """)

    # 4. business_projects — business goals/opportunities (renamed from 'projects')
    op.execute("""
        CREATE TABLE IF NOT EXISTS business_projects (
            id              TEXT PRIMARY KEY,
            name            TEXT NOT NULL,
            description     TEXT,
            businessGoal    TEXT,
            ownerId         TEXT,
            department      TEXT,
            status          TEXT DEFAULT 'Planning',
            priority        TEXT DEFAULT 'Medium',
            tags            TEXT,
            createdAt       TEXT,
            updatedAt       TEXT
        )
    """)

    # 5. project_agents — AI workers assigned to projects (renamed from 'agents')
    op.execute("""
        CREATE TABLE IF NOT EXISTS project_agents (
            id              TEXT PRIMARY KEY,
            projectId       TEXT,
            name            TEXT NOT NULL,
            status          TEXT NOT NULL,
            config          TEXT,
            systemPrompt    TEXT
        )
    """)

    # 6. execution_nodes — DAG execution graph
    op.execute("""
        CREATE TABLE IF NOT EXISTS execution_nodes (
            id              TEXT PRIMARY KEY,
            projectId       TEXT,
            agentId         TEXT,
            state           TEXT NOT NULL,
            dependencies    TEXT,
            outputs         TEXT,
            reasoning       TEXT
        )
    """)

    # 7. human_queue — human-in-the-loop approvals
    op.execute("""
        CREATE TABLE IF NOT EXISTS human_queue (
            id              TEXT PRIMARY KEY,
            projectId       TEXT,
            agentId         TEXT,
            reason          TEXT NOT NULL,
            status          TEXT NOT NULL,
            resolution      TEXT,
            assignedTo      TEXT
        )
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS human_queue")
    op.execute("DROP TABLE IF EXISTS execution_nodes")
    op.execute("DROP TABLE IF EXISTS project_agents")
    op.execute("DROP TABLE IF EXISTS business_projects")
    op.execute("DROP TABLE IF EXISTS auth_sessions")
    op.execute("DROP TABLE IF EXISTS users")
    op.execute("DROP TABLE IF EXISTS organization")

"""Per-project agent teams: project scoping, model column, and team status.

Adds the columns the BA-designed team feature needs:
  - agents.project_id  — scopes an agent org chart to one project
  - agents.model       — the ai_models model_id this agent runs on
  - business_projects.team_status — pending|generating|ready|failed (drives the
    workspace "assembling team" loading state)

Revision ID: 0022
Revises: 0021
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0022_agent_project_model"
down_revision: str | None = "0021_ba_agent_discovery"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE agents ADD COLUMN IF NOT EXISTS project_id TEXT")
    op.execute("ALTER TABLE agents ADD COLUMN IF NOT EXISTS model TEXT")
    op.execute(
        "ALTER TABLE business_projects ADD COLUMN IF NOT EXISTS team_status TEXT DEFAULT 'pending'"
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_agents_project_id ON agents (project_id)")


def downgrade() -> None:
    pass

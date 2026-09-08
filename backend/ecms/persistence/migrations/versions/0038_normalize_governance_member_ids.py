"""Normalize legacy governance owners to organization member IDs.

Older project assignments may reference permanent records from the agents table.
The project hierarchy now renders the canonical organization_members reporting
chain, so map those legacy IDs to the corresponding employee record by name.

Revision ID: 0038
Revises: 0037
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0038_normalize_governance_member_ids"
down_revision: str | None = "0037_expand_agent_certification_portfolios"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    if op.get_bind().dialect.name == "sqlite":
        # No UPDATE..FROM aliases or NOW() on sqlite; equivalent spelled plainly.
        op.execute(
            """
            UPDATE project_agent_governance_assignments
            SET organization_member_id = (
                SELECT members.id FROM agents AS permanent_agents
                JOIN organization_members AS members
                  ON LOWER(TRIM(members.name)) = LOWER(TRIM(permanent_agents.name))
                WHERE project_agent_governance_assignments.organization_member_id = permanent_agents.id
                  AND permanent_agents.project_id IS NULL
                  AND members.status = 'active'
                LIMIT 1
            ),
            updated_at = datetime('now')
            WHERE EXISTS (
                SELECT 1 FROM agents AS permanent_agents
                JOIN organization_members AS members
                  ON LOWER(TRIM(members.name)) = LOWER(TRIM(permanent_agents.name))
                WHERE project_agent_governance_assignments.organization_member_id = permanent_agents.id
                  AND permanent_agents.project_id IS NULL
                  AND members.status = 'active'
            )
            """
        )
        return
    op.execute(
        """
        UPDATE project_agent_governance_assignments AS governance
        SET organization_member_id = members.id,
            updated_at = NOW()
        FROM agents AS permanent_agents
        JOIN organization_members AS members
          ON LOWER(TRIM(members.name)) = LOWER(TRIM(permanent_agents.name))
        WHERE governance.organization_member_id = permanent_agents.id
          AND permanent_agents.project_id IS NULL
          AND members.status = 'active'
        """
    )


def downgrade() -> None:
    # Organization member IDs are the canonical ownership identifiers and should
    # not be changed back to the deprecated permanent-agent IDs.
    pass

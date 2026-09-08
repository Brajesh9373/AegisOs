"""Drop FK constraint on governance assignments organization_member_id.

Allows governance assignments to reference permanent agent IDs directly
from the agents table instead of requiring organization_members entries.

Revision ID: 0033
Revises: 0032
"""

from alembic import op

revision = "0033_governance_drop_member_fk"
down_revision = "0032_queue_ticket_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # SQLite neither enforces named FK constraints nor supports dropping
    # them; the constraint simply never exists there.
    if op.get_bind().dialect.name == "sqlite":
        return
    op.drop_constraint(
        "project_agent_governance_assignment_organization_member_id_fkey",
        "project_agent_governance_assignments",
        type_="foreignkey",
    )


def downgrade() -> None:
    op.create_foreign_key(
        "project_agent_governance_assignment_organization_member_id_fkey",
        "project_agent_governance_assignments",
        "organization_members",
        ["organization_member_id"],
        ["id"],
        ondelete="RESTRICT",
    )

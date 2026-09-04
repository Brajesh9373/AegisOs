"""Add ticket fields to human_queue table.

Revision ID: 0032
Revises: 0031
"""

import sqlalchemy as sa
from alembic import op

revision = "0032_queue_ticket_fields"
down_revision = "0031_agent_automation_features"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("human_queue", sa.Column("title", sa.Text(), nullable=True))
    op.add_column(
        "human_queue", sa.Column("type", sa.Text(), server_default="Approval", nullable=True)
    )
    op.add_column(
        "human_queue", sa.Column("priority", sa.Text(), server_default="Medium", nullable=True)
    )
    op.add_column(
        "human_queue", sa.Column("confidence", sa.Integer(), server_default="50", nullable=True)
    )
    op.add_column("human_queue", sa.Column("agent_name", sa.Text(), nullable=True))
    op.add_column(
        "human_queue", sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column("human_queue", sa.Column("due_by", sa.DateTime(timezone=True), nullable=True))
    op.add_column("human_queue", sa.Column("comment", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("human_queue", "comment")
    op.drop_column("human_queue", "due_by")
    op.drop_column("human_queue", "submitted_at")
    op.drop_column("human_queue", "agent_name")
    op.drop_column("human_queue", "confidence")
    op.drop_column("human_queue", "priority")
    op.drop_column("human_queue", "type")
    op.drop_column("human_queue", "title")

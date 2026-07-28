"""Agents, tasks, dependencies, and cross-team requests.

Revision ID: 0007
Revises: 0006
Create Date: 2026-07-11 00:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # agents
    op.create_table(
        "agents",
        sa.Column("id", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=64), nullable=False),
        sa.Column("designation", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("role_description", sa.Text(), nullable=True),
        sa.Column("skills", sa.JSON(), nullable=True),
        sa.Column("department", sa.String(length=128), nullable=False),
        sa.Column("reports_to", sa.String(length=128), nullable=True),
        sa.Column("tool_policy", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("workspace_scope", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("system_prompt_addon", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["reports_to"], ["agents.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agents_role", "agents", ["role"])
    op.create_index("ix_agents_department", "agents", ["department"])
    op.create_index("ix_agents_reports_to", "agents", ["reports_to"])
    op.create_index("ix_agents_status", "agents", ["status"])

    # tasks
    op.create_table(
        "tasks",
        sa.Column("id", sa.String(length=128), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("assigner_id", sa.String(length=128), nullable=False),
        sa.Column("assignee_id", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("priority", sa.String(length=32), nullable=False, server_default="normal"),
        sa.Column("inputs", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("expected_output", sa.Text(), nullable=True),
        sa.Column("output_files", sa.JSON(), nullable=True),
        sa.Column("output_summary", sa.Text(), nullable=True),
        sa.Column("review_feedback", sa.Text(), nullable=True),
        sa.Column("parent_task_id", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["assigner_id"], ["agents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["assignee_id"], ["agents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_task_id"], ["tasks.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tasks_assigner_id", "tasks", ["assigner_id"])
    op.create_index("ix_tasks_assignee_id", "tasks", ["assignee_id"])
    op.create_index("ix_tasks_status", "tasks", ["status"])
    op.create_index("ix_tasks_created_at", "tasks", ["created_at"])

    # cross_team_requests
    op.create_table(
        "cross_team_requests",
        sa.Column("id", sa.String(length=128), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("requester_id", sa.String(length=128), nullable=False),
        sa.Column("target_dept", sa.String(length=128), nullable=False),
        sa.Column("target_senior_id", sa.String(length=128), nullable=True),
        sa.Column("spawned_task_id", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("priority", sa.String(length=32), nullable=False, server_default="normal"),
        sa.Column("inputs", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("output", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["requester_id"], ["agents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_senior_id"], ["agents.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["spawned_task_id"], ["tasks.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_cross_team_requests_requester_id", "cross_team_requests", ["requester_id"])
    op.create_index("ix_cross_team_requests_target_dept", "cross_team_requests", ["target_dept"])
    op.create_index("ix_cross_team_requests_status", "cross_team_requests", ["status"])

    # task_dependencies
    op.create_table(
        "task_dependencies",
        sa.Column("id", sa.String(length=128), nullable=False),
        sa.Column("blocked_task_id", sa.String(length=128), nullable=False),
        sa.Column("blocker_task_id", sa.String(length=128), nullable=False),
        sa.Column("dependency_type", sa.String(length=32), nullable=False, server_default="same_team"),
        sa.Column("cross_team_request_id", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["blocked_task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["blocker_task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["cross_team_request_id"], ["cross_team_requests.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_task_dependencies_blocked_task_id", "task_dependencies", ["blocked_task_id"])
    op.create_index("ix_task_dependencies_blocker_task_id", "task_dependencies", ["blocker_task_id"])


def downgrade() -> None:
    op.drop_index("ix_task_dependencies_blocker_task_id", table_name="task_dependencies")
    op.drop_index("ix_task_dependencies_blocked_task_id", table_name="task_dependencies")
    op.drop_table("task_dependencies")
    op.drop_index("ix_cross_team_requests_status", table_name="cross_team_requests")
    op.drop_index("ix_cross_team_requests_target_dept", table_name="cross_team_requests")
    op.drop_index("ix_cross_team_requests_requester_id", table_name="cross_team_requests")
    op.drop_table("cross_team_requests")
    op.drop_index("ix_tasks_created_at", table_name="tasks")
    op.drop_index("ix_tasks_status", table_name="tasks")
    op.drop_index("ix_tasks_assignee_id", table_name="tasks")
    op.drop_index("ix_tasks_assigner_id", table_name="tasks")
    op.drop_table("tasks")
    op.drop_index("ix_agents_status", table_name="agents")
    op.drop_index("ix_agents_reports_to", table_name="agents")
    op.drop_index("ix_agents_department", table_name="agents")
    op.drop_index("ix_agents_role", table_name="agents")
    op.drop_table("agents")

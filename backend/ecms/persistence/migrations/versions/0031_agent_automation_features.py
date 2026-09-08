"""Add automation and features columns to agents table.

Revision ID: 0031
Revises: 0030
"""

import sqlalchemy as sa
from alembic import op

revision = "0031_agent_automation_features"
down_revision = "0030_seed_organization_members"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("agents", sa.Column("automation", sa.JSON(), nullable=True))
    op.add_column("agents", sa.Column("features", sa.JSON(), nullable=True))

    # SQLite has no ::json / ::text casts; the same statements work uncast
    # (JSON is stored as TEXT there).
    cast = "" if op.get_bind().dialect.name == "sqlite" else "::json"
    text_cast = "" if op.get_bind().dialect.name == "sqlite" else "::text"

    # Seed default automation + features for existing agents
    op.execute(f"""
        UPDATE agents SET
            automation = '{{"autoRetry": true, "maxRetries": 3, "retryDelaySeconds": 30, "escalateOnFailure": true, "heartbeatIntervalSeconds": 60}}'{cast},
            features = '{{"memoryRetentionDays": 30, "dataQueryAccess": "read", "maxConcurrentTasks": 5, "rateLimitPerMinute": 60, "streamingEnabled": true, "auditLogging": true, "piiMasking": false}}'{cast}
        WHERE automation IS NULL
    """)

    # Backfill skills for agents that have empty skills arrays.
    # Skills are now populated at creation time via the BA team design prompt,
    # but existing agents created before that fix need a one-time backfill.
    skill_map = {
        "delivery_manager": '["delivery management", "stakeholder coordination", "risk management", "sprint planning", "status reporting"]',
        "architect": '["system design", "architecture review", "technical planning", "solution modeling", "technology evaluation"]',
        "business_analyst": '["requirements management", "acceptance criteria", "scope control", "stakeholder interviews", "process mapping"]',
        "engineering_manager": '["engineering planning", "dependency management", "execution coordination", "resource allocation", "code review"]',
        "tech_lead": '["data modeling", "migration", "data validation", "ETL pipelines", "schema design"]',
        "engineer": '["backend engineering", "API design", "service integration", "database optimization", "debugging"]',
        "sre": '["infrastructure management", "CI/CD", "monitoring", "incident response", "automation"]',
        "security_engineer": '["security assessment", "compliance auditing", "access control", "encryption", "vulnerability scanning"]',
        "qa_engineer": '["test planning", "automation testing", "regression testing", "quality assurance", "defect tracking"]',
        "qa_lead": '["test leadership", "test strategy", "test coordination", "quality metrics", "release sign-off"]',
        "uat_lead": '["UAT coordination", "hypercare support", "user feedback", "go-live validation", "post-launch monitoring"]',
    }
    for role, skills in skill_map.items():
        op.execute(f"""
            UPDATE agents SET skills = '{skills}'{cast}
            WHERE role = '{role}' AND skills{text_cast} = '[]'
        """)


def downgrade() -> None:
    op.drop_column("agents", "features")
    op.drop_column("agents", "automation")

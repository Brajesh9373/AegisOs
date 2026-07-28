"""Add automation and features columns to agents table.

Revision ID: 0031
Revises: 0030
"""

from alembic import op
import sqlalchemy as sa

revision = "0031"
down_revision = "0030"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("agents", sa.Column("automation", sa.JSON(), nullable=True))
    op.add_column("agents", sa.Column("features", sa.JSON(), nullable=True))

    # Seed default automation + features for existing agents
    op.execute("""
        UPDATE agents SET
            automation = '{"autoRetry": true, "maxRetries": 3, "retryDelaySeconds": 30, "escalateOnFailure": true, "heartbeatIntervalSeconds": 60}'::json,
            features = '{"memoryRetentionDays": 30, "dataQueryAccess": "read", "maxConcurrentTasks": 5, "rateLimitPerMinute": 60, "streamingEnabled": true, "auditLogging": true, "piiMasking": false}'::json
        WHERE automation IS NULL
    """)

    # Backfill skills for agents that have empty skills arrays.
    # Skills are now populated at creation time via the BA team design prompt,
    # but existing agents created before that fix need a one-time backfill.
    skill_map = {
        'delivery_manager': '["delivery management", "stakeholder coordination", "risk management", "sprint planning", "status reporting"]',
        'architect': '["system design", "architecture review", "technical planning", "solution modeling", "technology evaluation"]',
        'business_analyst': '["requirements management", "acceptance criteria", "scope control", "stakeholder interviews", "process mapping"]',
        'engineering_manager': '["engineering planning", "dependency management", "execution coordination", "resource allocation", "code review"]',
        'tech_lead': '["data modeling", "migration", "data validation", "ETL pipelines", "schema design"]',
        'engineer': '["backend engineering", "API design", "service integration", "database optimization", "debugging"]',
        'sre': '["infrastructure management", "CI/CD", "monitoring", "incident response", "automation"]',
        'security_engineer': '["security assessment", "compliance auditing", "access control", "encryption", "vulnerability scanning"]',
        'qa_engineer': '["test planning", "automation testing", "regression testing", "quality assurance", "defect tracking"]',
        'qa_lead': '["test leadership", "test strategy", "test coordination", "quality metrics", "release sign-off"]',
        'uat_lead': '["UAT coordination", "hypercare support", "user feedback", "go-live validation", "post-launch monitoring"]',
    }
    for role, skills in skill_map.items():
        op.execute(f"""
            UPDATE agents SET skills = '{skills}'::json
            WHERE role = '{role}' AND skills::text = '[]'
        """)


def downgrade() -> None:
    op.drop_column("agents", "features")
    op.drop_column("agents", "automation")

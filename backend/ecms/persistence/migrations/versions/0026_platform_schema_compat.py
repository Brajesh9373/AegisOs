"""Add compatibility columns for platform audit and artifact tables.

Revision ID: 0026
Revises: 0025
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
from sqlalchemy import text

revision: str = "0026_platform_schema_compat"
down_revision: str | None = "0025_knowledge"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _column_exists(table: str, column: str) -> bool:
    """Check whether a column exists on a table."""
    conn = op.get_bind()
    res = conn.execute(
        text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name = :tbl AND column_name = :col"
        ),
        {"tbl": table, "col": column},
    )
    return res.fetchone() is not None


def upgrade() -> None:
    # audit_logs – add new columns, then back-fill from legacy names if they exist
    op.execute("ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS details TEXT")
    op.execute("ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS timestamp TEXT")

    # Only back-fill when the legacy source columns are present.
    # On fresh databases the tables are created with the new names directly,
    # so the old columns (detail, createdat) never exist.
    if _column_exists("audit_logs", "detail"):
        op.execute(
            text(
                "UPDATE audit_logs SET details = detail "
                "WHERE details IS NULL AND detail IS NOT NULL"
            )
        )
    if _column_exists("audit_logs", "createdat"):
        op.execute(
            text(
                "UPDATE audit_logs SET timestamp = createdat "
                "WHERE timestamp IS NULL AND createdat IS NOT NULL"
            )
        )

    # artifacts – add new columns, then back-fill from legacy name if it exists
    op.execute("ALTER TABLE artifacts ADD COLUMN IF NOT EXISTS storagepath TEXT")
    op.execute("ALTER TABLE artifacts ADD COLUMN IF NOT EXISTS versionhistory TEXT")

    if _column_exists("artifacts", "uri"):
        op.execute(
            text(
                "UPDATE artifacts SET storagepath = uri "
                "WHERE storagepath IS NULL AND uri IS NOT NULL"
            )
        )


def downgrade() -> None:
    op.execute("ALTER TABLE artifacts DROP COLUMN IF EXISTS versionhistory")
    op.execute("ALTER TABLE artifacts DROP COLUMN IF EXISTS storagepath")
    op.execute("ALTER TABLE audit_logs DROP COLUMN IF EXISTS timestamp")
    op.execute("ALTER TABLE audit_logs DROP COLUMN IF EXISTS details")

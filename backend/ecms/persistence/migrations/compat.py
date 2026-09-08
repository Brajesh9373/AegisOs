"""Compatibility helpers for migrations across postgres and sqlite.

Production runs postgres; development and tests run sqlite. SQLite lacks
`ADD COLUMN IF NOT EXISTS` (and any `DROP CONSTRAINT`), so migrations that
need those spellings branch here instead of duplicating dialect logic.
Postgres behavior is byte-identical to the original statements.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

__all__ = ["add_column_if_missing", "drop_constraint_if_exists"]


def add_column_if_missing(table: str, column_ddl: str) -> None:
    """Add a column only when absent.

    Args:
        table: Table name.
        column_ddl: Column definition as it would appear after ADD COLUMN,
            e.g. `"connector_type TEXT"` (defaults included).
    """
    bind = op.get_bind()
    if bind.dialect.name != "sqlite":
        op.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column_ddl}")
        return
    name = column_ddl.split()[0].strip('"')
    existing = {column["name"] for column in sa.inspect(bind).get_columns(table)}
    if name not in existing:
        op.execute(f"ALTER TABLE {table} ADD COLUMN {column_ddl}")


def drop_constraint_if_exists(table: str, constraint: str) -> None:
    """Drop a named constraint; no-op on sqlite (no DROP CONSTRAINT support)."""
    if op.get_bind().dialect.name == "sqlite":
        return
    op.execute(f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS {constraint}")

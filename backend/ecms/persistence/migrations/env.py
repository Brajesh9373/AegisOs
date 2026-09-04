"""Alembic migration environment (SECTION 81)."""

from __future__ import annotations

import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from ecms.persistence.models import (
    access_policy,  # noqa: F401  (registers policy models)
    agent,  # noqa: F401  (registers agent models)
    audit,  # noqa: F401  (registers the model metadata)
    ba_stage_outcome,  # noqa: F401  (registers BA durability models)
    category,  # noqa: F401  (registers category models)
    governance_assignment,  # noqa: F401  (registers governance models)
    organization_member,  # noqa: F401  (registers org member models)
    project,  # noqa: F401  (registers project models)
    project_agent_position,  # noqa: F401  (registers project staffing models)
    session,  # noqa: F401  (registers session models)
    session_context,  # noqa: F401  (registers session context KV)
    task,  # noqa: F401  (registers task/dependency/CTR models)
)
from ecms.persistence.models.base import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _database_url() -> str:
    return os.environ.get("ECMS_DATABASE_URL") or config.get_main_option("sqlalchemy.url", "")


def run_migrations_offline() -> None:
    """Run migrations in offline mode, emitting SQL statements."""
    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def _run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in online mode against an async engine."""
    engine = create_async_engine(_database_url())
    async with engine.connect() as connection:
        await connection.run_sync(_run_migrations)
    await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())

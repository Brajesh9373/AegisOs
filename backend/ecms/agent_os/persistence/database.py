"""Agent OS persistence database utilities.

Provides database session management for Agent OS repositories.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from ecms.configuration.schemas.settings import get_settings

__all__ = ["db_session", "get_engine", "init_agent_os_db"]


def get_engine():
    """Get or create the async database engine."""
    settings = get_settings()
    database_url = settings.database_url

    # Convert sync URL to async if needed
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("sqlite://"):
        database_url = database_url.replace("sqlite://", "sqlite+aiosqlite://", 1)

    return create_async_engine(database_url, echo=False)


_engine = None
_session_factory = None


def init_agent_os_db():
    """Initialize the database engine and session factory."""
    global _engine, _session_factory
    if _engine is None:
        _engine = get_engine()
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            _engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )


@asynccontextmanager
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional scope for database operations."""
    if _session_factory is None:
        init_agent_os_db()

    async with _session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

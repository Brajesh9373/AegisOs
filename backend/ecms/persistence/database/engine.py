"""Async database engine and session management (SECTION 81)."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from ecms.persistence.models.base import Base

__all__ = ["Database"]


class Database:
    """Owns the async engine and session factory for a database URL (SECTION 81)."""

    def __init__(self, url: str, *, echo: bool = False) -> None:
        """Initialize the async engine and session factory for the given URL."""
        self._engine = create_async_engine(url, echo=echo)
        self._session_factory = async_sessionmaker(self._engine, expire_on_commit=False)

    async def create_all(self) -> None:
        """Create all tables (development/test convenience; use migrations in production)."""
        async with self._engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    def new_session(self) -> AsyncSession:
        """Return a new session for callers that manage their own transaction.

        Unlike :meth:`session`, this does not commit automatically; the caller (for
        example the Unit of Work) is responsible for commit, rollback and close.
        """
        return self._session_factory()

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        """Yield a transactional session, committing on success and rolling back on error."""
        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def dispose(self) -> None:
        """Dispose the engine's connection pool."""
        await self._engine.dispose()

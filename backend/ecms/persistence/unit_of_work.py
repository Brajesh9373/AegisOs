"""Unit of Work: a transactional boundary over one session (SECTION 252).

A unit of work opens a single session, hands out repositories bound to it, and
commits or rolls back atomically. Domain events collected from aggregates are
buffered on the unit of work so the application layer can publish them after a
successful commit.
"""

from __future__ import annotations

from types import TracebackType
from typing import Self

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ecms.persistence.database.engine import Database
from ecms.persistence.repositories.aggregate import AggregateRepository
from ecms.shared.exceptions import RepositoryError
from ecms.shared.models import AggregateRoot

__all__ = ["UnitOfWork"]


class UnitOfWork:
    """Transactional boundary providing repositories over a single session (SECTION 252)."""

    def __init__(self, database: Database) -> None:
        """Initialize the unit of work against a database."""
        self._database = database
        self._session: AsyncSession | None = None
        self.pending_events: list[object] = []

    @property
    def session(self) -> AsyncSession:
        """Return the active session, or raise if the unit of work is not entered."""
        if self._session is None:
            raise RepositoryError("unit of work is not active")
        return self._session

    async def __aenter__(self) -> Self:
        """Open a new session for the transaction."""
        self._session = self._database.new_session()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Commit on success, roll back on error, and always close the session."""
        try:
            if exc_type is not None:
                await self.rollback()
            else:
                await self.commit()
        finally:
            await self.session.close()
            self._session = None

    async def commit(self) -> None:
        """Commit the current transaction."""
        await self.session.commit()

    async def rollback(self) -> None:
        """Roll back the current transaction."""
        await self.session.rollback()

    def repository[T: BaseModel](
        self, model_type: type[T], *, aggregate_type: str, id_attr: str
    ) -> AggregateRepository[T]:
        """Return a repository for ``model_type`` bound to this session."""
        return AggregateRepository(
            self.session, model_type, aggregate_type=aggregate_type, id_attr=id_attr
        )

    def collect_events(self, aggregate: AggregateRoot) -> None:
        """Buffer the domain events pending on an aggregate for later publication."""
        self.pending_events.extend(aggregate.collect_events())

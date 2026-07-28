"""Generic repository over persisted aggregate documents (SECTION 251/255/259).

The repository exposes domain models and hides storage entirely. Queries are
scoped to an organization when one is supplied, enforcing tenant isolation, and
deletion is soft by default: hard deletion requires explicit governance approval.
"""

from __future__ import annotations

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ecms.persistence.models.aggregate import AggregateRecord
from ecms.shared.exceptions import ConflictError, RepositoryError
from ecms.shared.time import utcnow

__all__ = ["AggregateRepository"]

_DELETED = "deleted"
_ACTIVE = "active"


class AggregateRepository[T: BaseModel]:
    """Persists Pydantic aggregates of one type as versioned JSON documents.

    Args:
        session: The active async session.
        model_type: The concrete aggregate model class.
        aggregate_type: The stable type discriminator stored on each record.
        id_attr: The name of the aggregate's identity attribute (for example
            ``"task_id"``).
    """

    def __init__(
        self,
        session: AsyncSession,
        model_type: type[T],
        *,
        aggregate_type: str,
        id_attr: str,
    ) -> None:
        """Initialize the repository for a concrete aggregate type."""
        self._session = session
        self._model_type = model_type
        self._aggregate_type = aggregate_type
        self._id_attr = id_attr

    def _identity(self, entity: T) -> str:
        return str(getattr(entity, self._id_attr))

    async def _fetch(
        self,
        entity_id: str,
        *,
        organization_id: str | None,
        include_deleted: bool,
    ) -> AggregateRecord | None:
        stmt = select(AggregateRecord).where(
            AggregateRecord.id == entity_id,
            AggregateRecord.aggregate_type == self._aggregate_type,
        )
        if organization_id is not None:
            stmt = stmt.where(AggregateRecord.organization_id == organization_id)
        if not include_deleted:
            stmt = stmt.where(AggregateRecord.lifecycle_state != _DELETED)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def add(self, entity: T) -> T:
        """Persist a new aggregate.

        Raises:
            ConflictError: If an aggregate with the same id already exists.
        """
        entity_id = self._identity(entity)
        existing = await self._fetch(entity_id, organization_id=None, include_deleted=True)
        if existing is not None:
            raise ConflictError(f"aggregate {entity_id!r} already exists")
        record = AggregateRecord(
            id=entity_id,
            aggregate_type=self._aggregate_type,
            organization_id=getattr(entity, "organization_id", None),
            workspace_id=getattr(entity, "workspace_id", None),
            project_id=getattr(entity, "project_id", None),
            version=1,
            lifecycle_state=_ACTIVE,
            data=entity.model_dump(mode="json"),
        )
        self._session.add(record)
        await self._session.flush()
        return entity

    async def get(self, entity_id: str, *, organization_id: str | None = None) -> T | None:
        """Return the aggregate with ``entity_id``, or ``None`` if absent or deleted."""
        record = await self._fetch(
            entity_id, organization_id=organization_id, include_deleted=False
        )
        if record is None:
            return None
        return self._model_type.model_validate(record.data)

    async def update(self, entity: T) -> T:
        """Persist changes to an existing aggregate, bumping its version.

        Raises:
            RepositoryError: If the aggregate does not exist.
        """
        entity_id = self._identity(entity)
        record = await self._fetch(entity_id, organization_id=None, include_deleted=True)
        if record is None:
            raise RepositoryError(f"aggregate {entity_id!r} does not exist")
        record.data = entity.model_dump(mode="json")
        record.version += 1
        record.updated_at = utcnow()
        await self._session.flush()
        return entity

    async def remove(self, entity_id: str) -> None:
        """Soft-delete the aggregate; never a silent hard delete (SECTION 255)."""
        record = await self._fetch(entity_id, organization_id=None, include_deleted=False)
        if record is None:
            return
        record.lifecycle_state = _DELETED
        record.updated_at = utcnow()
        await self._session.flush()

    async def purge(self, entity_id: str, *, governance_approved: bool) -> None:
        """Permanently delete an aggregate; requires governance approval (SECTION 255).

        Raises:
            RepositoryError: If ``governance_approved`` is not ``True``.
        """
        if not governance_approved:
            raise RepositoryError("hard delete requires governance approval")
        record = await self._fetch(entity_id, organization_id=None, include_deleted=True)
        if record is not None:
            await self._session.delete(record)
            await self._session.flush()

    async def list_all(
        self, *, organization_id: str | None = None, include_deleted: bool = False
    ) -> list[T]:
        """Return all aggregates, optionally scoped to an organization."""
        stmt = select(AggregateRecord).where(AggregateRecord.aggregate_type == self._aggregate_type)
        if organization_id is not None:
            stmt = stmt.where(AggregateRecord.organization_id == organization_id)
        if not include_deleted:
            stmt = stmt.where(AggregateRecord.lifecycle_state != _DELETED)
        result = await self._session.execute(stmt.order_by(AggregateRecord.created_at))
        return [self._model_type.model_validate(record.data) for record in result.scalars().all()]

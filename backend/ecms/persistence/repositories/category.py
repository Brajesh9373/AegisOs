"""Category taxonomy repository.

CRUD for user-defined technical domains. Defaults are seeded by migration 0012.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ecms.persistence.models.category import Category


class CategoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self) -> list[Category]:
        stmt = select(Category).order_by(Category.priority.asc(), Category.name.asc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_active(self) -> list[Category]:
        """All categories (taxonomy is fully user-owned; none are 'inactive')."""
        return await self.list_all()

    async def get_by_name(self, name: str) -> Category | None:
        stmt = select(Category).where(Category.name == name)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get(self, category_id: str) -> Category | None:
        stmt = select(Category).where(Category.id == category_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self, *, name: str, description: str, color: str, priority: int
    ) -> Category:
        cat = Category(
            id=f"cat-{name}",
            name=name,
            description=description,
            color=color,
            priority=priority,
            is_default=False,
        )
        self._session.add(cat)
        await self._session.flush()
        return cat

    async def update(
        self, category: Category, *, description: str | None = None,
        color: str | None = None, priority: int | None = None, name: str | None = None,
    ) -> Category:
        if description is not None:
            category.description = description
        if color is not None:
            category.color = color
        if priority is not None:
            category.priority = priority
        if name is not None:
            category.name = name
        return category

    async def delete(self, category: Category) -> None:
        # Guard: never delete the catch-all
        if category.name == "uncategorized":
            raise ValueError("Cannot delete the 'uncategorized' catch-all")
        await self._session.delete(category)

    def to_dict_list(self, cats: list[Category]) -> list[dict[str, Any]]:
        return [c.to_dict() for c in cats]

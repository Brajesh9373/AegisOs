"""Category taxonomy REST API.

User-defined technical domains used by the categorization agent. Defaults are
seeded by migration 0012; users can add/edit/delete via this API.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ecms.persistence.database.rest_session import db_session

router = APIRouter(prefix="/categories", tags=["categories"])


class CategoryCreate(BaseModel):
    name: str
    description: str
    color: str = "#94a3b8"
    priority: int = 99


class CategoryUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    color: str | None = None
    priority: int | None = None


@router.get("")
async def list_categories():
    from ecms.persistence.repositories.category import CategoryRepository

    async with db_session() as s:
        cats = await CategoryRepository(s).list_all()
        return [c.to_dict() for c in cats]


@router.post("")
async def create_category(body: CategoryCreate):
    from ecms.persistence.repositories.category import CategoryRepository

    async with db_session() as s:
        repo = CategoryRepository(s)
        if await repo.get_by_name(body.name):
            raise HTTPException(status_code=409, detail=f"Category '{body.name}' already exists")
        cat = await repo.create(
            name=body.name, description=body.description, color=body.color, priority=body.priority
        )
        await s.commit()
        await s.refresh(cat)
        return cat.to_dict()


@router.put("/{category_id}")
async def update_category(category_id: str, body: CategoryUpdate):
    from ecms.persistence.repositories.category import CategoryRepository

    async with db_session() as s:
        repo = CategoryRepository(s)
        cat = await repo.get(category_id)
        if not cat:
            raise HTTPException(status_code=404, detail="Category not found")
        cat = await repo.update(
            cat, description=body.description, color=body.color,
            priority=body.priority, name=body.name,
        )
        await s.commit()
        await s.refresh(cat)
        return cat.to_dict()


@router.delete("/{category_id}")
async def delete_category(category_id: str):
    from ecms.persistence.repositories.category import CategoryRepository

    async with db_session() as s:
        repo = CategoryRepository(s)
        cat = await repo.get(category_id)
        if not cat:
            raise HTTPException(status_code=404, detail="Category not found")
        try:
            await repo.delete(cat)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        await s.commit()
        return {"deleted": True, "id": category_id}


@router.post("/categorize/{workspace_id}")
async def recategorize(workspace_id: str):
    """Trigger AI categorization as a background task."""
    import asyncio
    from ecms.agent.categorize import run_categorization
    asyncio.create_task(run_categorization(workspace_id, workspace_id))
    return {"status": "categorization_started", "workspace_id": workspace_id}

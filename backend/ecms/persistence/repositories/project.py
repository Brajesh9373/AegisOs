"""Project persistence repository.

Handles CRUD for projects and their connectors in PostgreSQL. This is the
source-of-truth for project metadata — the graph (FalkorDB) holds derived
knowledge, not configuration.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ecms.persistence.models.project import Project, ProjectConnector


class ProjectRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(
        self,
        *,
        project_id: str,
        workspace_id: str,
        name: str,
        group_id: str | None = None,
        description: str | None = None,
        connectors: list[dict[str, Any]] | None = None,
        replace_connectors: bool = False,
    ) -> Project:
        stmt = select(Project).where(Project.workspace_id == workspace_id)
        result = await self._session.execute(stmt)
        project = result.scalar_one_or_none()

        if project is None:
            project = Project(
                id=f"proj:{workspace_id}",
                name=name,
                description=description,
                workspace_id=workspace_id,
                group_id=group_id,
            )
            self._session.add(project)
        else:
            project.name = name
            if description is not None:
                project.description = description
            if group_id is not None and group_id != project.group_id:
                project.group_id = group_id

        if connectors is not None:
            if replace_connectors:
                existing = select(ProjectConnector).where(
                    ProjectConnector.project_id == project.id,
                )
                existing_conns = (await self._session.execute(existing)).scalars().all()
                for ec in existing_conns:
                    await self._session.delete(ec)

            for conn in connectors:
                # Check if a connector of this type+key already exists
                ctype = conn["type"]
                ckey = conn.get("config", {}).get("key", conn.get("config", {}).get("repo_url", ""))
                persist_path = conn.get("persist_path")
                if ckey:
                    dup_stmt = select(ProjectConnector).where(
                        ProjectConnector.project_id == project.id,
                        ProjectConnector.connector_type == ctype,
                    )
                    dup_conns = (await self._session.execute(dup_stmt)).scalars().all()
                    for dc in dup_conns:
                        if dc.config.get("repo_url") == ckey or dc.config.get("host") == ckey:
                            dc.config = conn.get("config", {})
                            if persist_path is not None:
                                dc.persist_path = persist_path
                            break
                    else:
                        pc = ProjectConnector(
                            project_id=project.id,
                            connector_type=ctype,
                            config=conn.get("config", {}),
                            persist_path=persist_path,
                        )
                        self._session.add(pc)
                else:
                    pc = ProjectConnector(
                        project_id=project.id,
                        connector_type=ctype,
                        config=conn.get("config", {}),
                        persist_path=persist_path,
                    )
                    self._session.add(pc)

        return project

    async def get_by_workspace(self, workspace_id: str) -> Project | None:
        stmt = select(Project).where(Project.workspace_id == workspace_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Project | None:
        stmt = select(Project).where(Project.name == name)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self) -> list[Project]:
        stmt = select(Project).order_by(Project.created_at.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def delete(self, workspace_id: str) -> bool:
        stmt = delete(Project).where(Project.workspace_id == workspace_id)
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.rowcount > 0

    async def export_all(self) -> list[dict[str, Any]]:
        projects = await self.list_all()
        out: list[dict[str, Any]] = []
        for p in projects:
            conn_stmt = select(ProjectConnector).where(
                ProjectConnector.project_id == p.id,
            )
            conns = (await self._session.execute(conn_stmt)).scalars().all()
            out.append(
                {
                    "project_id": p.workspace_id,
                    "name": p.name,
                    "description": p.description,
                    "group_id": p.group_id,
                    "created_at": p.created_at.isoformat() if p.created_at else "",
                    "connectors": [
                        {
                            "type": c.connector_type,
                            "config": c.config,
                            "persist_path": c.persist_path,
                        }
                        for c in conns
                    ],
                }
            )
        return out

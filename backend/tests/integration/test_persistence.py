"""Integration tests for the persistence layer."""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path

import pytest
import pytest_asyncio

from ecms.persistence import (
    AuditRecord,
    AuditRepository,
    Database,
    Saga,
    SagaError,
    UnitOfWork,
)
from ecms.shared.enums import AgentRole
from ecms.shared.exceptions import ConflictError, RepositoryError
from ecms.shared.models import Agent, Task


@pytest_asyncio.fixture
async def database(tmp_path: Path) -> AsyncIterator[Database]:
    db = Database(f"sqlite+aiosqlite:///{tmp_path.as_posix()}/test.db")
    await db.create_all()
    yield db
    await db.dispose()


async def test_audit_add_and_query(database: Database) -> None:
    async with database.session() as session:
        repository = AuditRepository(session)
        await repository.add(
            AuditRecord(actor="alice", action="login", resource="auth", outcome="success"),
        )
        await repository.add(
            AuditRecord(actor="alice", action="read", resource="doc", outcome="success"),
        )
        await repository.add(
            AuditRecord(actor="bob", action="login", resource="auth", outcome="failed"),
        )

    async with database.session() as session:
        repository = AuditRepository(session)
        alice_records = await repository.list_by_actor("alice")
        assert len(alice_records) == 2
        assert await repository.count() == 3


async def test_session_rolls_back_on_error(database: Database) -> None:
    with pytest.raises(ValueError, match="boom"):
        async with database.session() as session:
            session.add(AuditRecord(actor="x", action="a", resource="r", outcome="o"))
            raise ValueError("boom")

    async with database.session() as session:
        assert await AuditRepository(session).count() == 0


def _task(organization_id: str = "org-1", title: str = "t") -> Task:
    return Task(
        session_id="session-1",
        organization_id=organization_id,
        user_id="user-1",
        title=title,
        goal="ship it",
    )


async def test_aggregate_add_get_update_round_trip(database: Database) -> None:
    task = _task()
    async with UnitOfWork(database) as uow:
        repo = uow.repository(Task, aggregate_type="task", id_attr="task_id")
        await repo.add(task)
    async with UnitOfWork(database) as uow:
        repo = uow.repository(Task, aggregate_type="task", id_attr="task_id")
        loaded = await repo.get(task.task_id)
        assert loaded is not None
        loaded.title = "renamed"
        await repo.update(loaded)
    async with UnitOfWork(database) as uow:
        repo = uow.repository(Task, aggregate_type="task", id_attr="task_id")
        again = await repo.get(task.task_id)
        assert again is not None
        assert again.title == "renamed"


async def test_tenant_scoping_isolates_organizations(database: Database) -> None:
    org_a = _task(organization_id="org-a", title="a")
    org_b = _task(organization_id="org-b", title="b")
    async with UnitOfWork(database) as uow:
        repo = uow.repository(Task, aggregate_type="task", id_attr="task_id")
        await repo.add(org_a)
        await repo.add(org_b)
    async with UnitOfWork(database) as uow:
        repo = uow.repository(Task, aggregate_type="task", id_attr="task_id")
        only_a = await repo.list_all(organization_id="org-a")
        assert [task.title for task in only_a] == ["a"]
        assert await repo.get(org_b.task_id, organization_id="org-a") is None


async def test_soft_delete_and_governed_purge(database: Database) -> None:
    task = _task()
    async with UnitOfWork(database) as uow:
        repo = uow.repository(Task, aggregate_type="task", id_attr="task_id")
        await repo.add(task)
        await repo.remove(task.task_id)
    async with UnitOfWork(database) as uow:
        repo = uow.repository(Task, aggregate_type="task", id_attr="task_id")
        assert await repo.get(task.task_id) is None
        assert len(await repo.list_all(include_deleted=True)) == 1
        with pytest.raises(RepositoryError):
            await repo.purge(task.task_id, governance_approved=False)
        await repo.purge(task.task_id, governance_approved=True)
        assert len(await repo.list_all(include_deleted=True)) == 0


async def test_duplicate_add_raises_conflict(database: Database) -> None:
    task = _task()
    async with UnitOfWork(database) as uow:
        repo = uow.repository(Task, aggregate_type="task", id_attr="task_id")
        await repo.add(task)
        with pytest.raises(ConflictError):
            await repo.add(task)


async def test_aggregate_without_tenant_is_supported(database: Database) -> None:
    async with UnitOfWork(database) as uow:
        repo = uow.repository(Agent, aggregate_type="agent", id_attr="agent_id")
        agent = Agent(role=AgentRole.PLANNER)
        await repo.add(agent)
        loaded = await repo.get(agent.agent_id)
        assert loaded is not None
        assert loaded.role is AgentRole.PLANNER


async def test_unit_of_work_rolls_back_on_error(database: Database) -> None:
    task = _task()
    with pytest.raises(RuntimeError):
        async with UnitOfWork(database) as uow:
            repo = uow.repository(Task, aggregate_type="task", id_attr="task_id")
            await repo.add(task)
            raise RuntimeError("boom")
    async with UnitOfWork(database) as uow:
        repo = uow.repository(Task, aggregate_type="task", id_attr="task_id")
        assert await repo.get(task.task_id) is None


async def test_saga_executes_all_steps_in_order() -> None:
    log: list[str] = []

    async def step_one() -> str:
        log.append("s1")
        return "r1"

    async def step_two() -> str:
        log.append("s2")
        return "r2"

    saga = Saga("demo").add_step("one", step_one).add_step("two", step_two)
    results = await saga.execute()
    assert results == ["r1", "r2"]
    assert log == ["s1", "s2"]


async def test_saga_compensates_completed_steps_on_failure() -> None:
    log: list[str] = []

    async def action_one() -> None:
        log.append("s1")

    async def compensate_one() -> None:
        log.append("c1")

    async def action_two() -> None:
        raise RuntimeError("boom")

    saga = Saga("demo").add_step("one", action_one, compensate_one).add_step("two", action_two)
    with pytest.raises(SagaError):
        await saga.execute()
    assert log == ["s1", "c1"]

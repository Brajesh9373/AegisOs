"""Task manager: task lifecycle, hierarchy and scheduling (SECTION 20/72).

Owns the state machine of a task from creation through completion, including the
parent/child hierarchy used for decomposed work. Emits a task event at every
transition.
"""

from __future__ import annotations

from ecms.events import EventBus
from ecms.runtime.events.runtime_events import (
    task_cancelled,
    task_completed,
    task_created,
    task_failed,
    task_started,
)
from ecms.shared.enums import TaskPriority, TaskStatus
from ecms.shared.events import BaseEvent
from ecms.shared.exceptions import NotFoundError
from ecms.shared.models import Task
from ecms.shared.time import utcnow

__all__ = ["TaskManager"]


class TaskManager:
    """Owns task lifecycle, dependencies and hierarchy (SECTION 72)."""

    def __init__(self, *, event_bus: EventBus | None = None) -> None:
        """Initialize an empty task registry."""
        self._tasks: dict[str, Task] = {}
        self._event_bus = event_bus

    async def create(
        self,
        *,
        session_id: str,
        organization_id: str,
        user_id: str,
        goal: str,
        title: str | None = None,
        parent_task: str | None = None,
        priority: TaskPriority = TaskPriority.MEDIUM,
    ) -> Task:
        """Create a task, linking it to a parent when one is given (SECTION 20)."""
        task = Task(
            session_id=session_id,
            organization_id=organization_id,
            user_id=user_id,
            title=title or goal[:80],
            goal=goal,
            priority=priority,
            parent_task=parent_task,
        )
        self._tasks[task.task_id] = task
        parent = self._tasks.get(parent_task) if parent_task else None
        if parent is not None:
            parent.child_tasks = [*parent.child_tasks, task.task_id]
        await self._emit(task_created(task.task_id))
        return task

    async def start(self, task_id: str) -> Task:
        """Transition a task to running."""
        task = self._require(task_id)
        task.status = TaskStatus.RUNNING
        task.started_at = utcnow()
        await self._emit(task_started(task_id))
        return task

    async def complete(self, task_id: str, *, summary: str | None = None) -> Task:
        """Transition a task to completed."""
        task = self._require(task_id)
        task.status = TaskStatus.COMPLETED
        task.completed_at = utcnow()
        if summary is not None:
            task.summary = summary
        await self._emit(task_completed(task_id))
        return task

    async def fail(self, task_id: str, error: str) -> Task:
        """Transition a task to failed and record the error."""
        task = self._require(task_id)
        task.status = TaskStatus.FAILED
        task.completed_at = utcnow()
        task.errors = [*task.errors, error]
        await self._emit(task_failed(task_id, error))
        return task

    async def cancel(self, task_id: str) -> Task:
        """Cancel a task."""
        task = self._require(task_id)
        task.status = TaskStatus.CANCELLED
        task.completed_at = utcnow()
        await self._emit(task_cancelled(task_id))
        return task

    async def retry(self, task_id: str) -> Task:
        """Requeue a failed task for another attempt (SECTION 294)."""
        task = self._require(task_id)
        task.status = TaskStatus.QUEUED
        task.completed_at = None
        return task

    def get(self, task_id: str) -> Task | None:
        """Return a task by id, or ``None``."""
        return self._tasks.get(task_id)

    def children(self, task_id: str) -> list[Task]:
        """Return the child tasks of a task."""
        parent = self._tasks.get(task_id)
        if parent is None:
            return []
        return [self._tasks[child] for child in parent.child_tasks if child in self._tasks]

    def _require(self, task_id: str) -> Task:
        task = self._tasks.get(task_id)
        if task is None:
            raise NotFoundError(f"task {task_id!r} not found")
        return task

    async def _emit(self, event: BaseEvent) -> None:
        if self._event_bus is not None:
            await self._event_bus.publish(event)

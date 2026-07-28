"""Tests for the tool manager pipeline and registry (SECTION 172/174)."""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from ecms.events import InMemoryEventBus
from ecms.shared.enums import EventCategory, ToolExecutionStatus
from ecms.shared.events import BaseEvent
from ecms.shared.exceptions import NotFoundError
from ecms.tools import (
    FilesystemTool,
    HttpTool,
    ToolManager,
    ToolPermissionEngine,
    ToolRegistry,
    ToolRequest,
    WorkspaceSandbox,
)


async def test_manager_executes_and_audits(tmp_path: Path) -> None:
    bus = InMemoryEventBus()
    seen: list[str] = []

    async def handler(event: BaseEvent) -> None:
        seen.append(event.event_type)

    bus.subscribe(handler, category=EventCategory.TOOL)
    manager = ToolManager(event_bus=bus)
    manager.register(FilesystemTool(WorkspaceSandbox(tmp_path)))
    execution = await manager.execute(
        "filesystem",
        ToolRequest(operation="write", arguments={"path": "f.txt", "content": "hi"}),
        task_id="task-1",
    )
    assert execution.status is ToolExecutionStatus.SUCCEEDED
    assert execution.artifacts
    assert execution.duration_ms is not None
    assert "ToolExecutionStarted" in seen
    assert "ToolExecutionCompleted" in seen
    assert "ToolArtifactGenerated" in seen


async def test_manager_denies_without_permission(tmp_path: Path) -> None:
    manager = ToolManager(permissions=ToolPermissionEngine(default_allow=False))
    manager.register(FilesystemTool(WorkspaceSandbox(tmp_path)))
    execution = await manager.execute(
        "filesystem", ToolRequest(operation="exists", arguments={"path": "x"})
    )
    assert execution.status is ToolExecutionStatus.DENIED


async def test_manager_records_tool_failure(tmp_path: Path) -> None:
    manager = ToolManager()
    manager.register(FilesystemTool(WorkspaceSandbox(tmp_path)))
    execution = await manager.execute(
        "filesystem", ToolRequest(operation="read", arguments={"path": "missing.txt"})
    )
    assert execution.status is ToolExecutionStatus.FAILED


def test_registry_missing_tool_raises() -> None:
    registry = ToolRegistry()
    with pytest.raises(NotFoundError):
        registry.get("nope")


async def test_http_tool_with_mock_transport() -> None:
    def responder(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"ok": True})

    client = httpx.AsyncClient(transport=httpx.MockTransport(responder))
    tool = HttpTool(client=client)
    result = await tool.execute(
        ToolRequest(operation="get", arguments={"url": "https://example.com/api"})
    )
    assert result.success
    assert result.output["status_code"] == 200
    await client.aclose()

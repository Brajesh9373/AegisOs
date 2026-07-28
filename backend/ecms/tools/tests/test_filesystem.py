"""Tests for the sandboxed filesystem tool (SECTION 80/177)."""

from __future__ import annotations

from pathlib import Path

import pytest

from ecms.shared.exceptions import AuthorizationError, ValidationError
from ecms.tools import FilesystemTool, ToolRequest, WorkspaceSandbox


def _tool(tmp_path: Path) -> FilesystemTool:
    return FilesystemTool(WorkspaceSandbox(tmp_path / "workspace"))


async def test_write_read_exists_delete(tmp_path: Path) -> None:
    tool = _tool(tmp_path)
    written = await tool.execute(
        ToolRequest(operation="write", arguments={"path": "a/b.txt", "content": "hi"})
    )
    assert written.success
    assert written.artifacts
    read = await tool.execute(ToolRequest(operation="read", arguments={"path": "a/b.txt"}))
    assert read.output == "hi"
    exists = await tool.execute(ToolRequest(operation="exists", arguments={"path": "a/b.txt"}))
    assert exists.output is True
    deleted = await tool.execute(ToolRequest(operation="delete", arguments={"path": "a/b.txt"}))
    assert deleted.success


async def test_append_list_and_search(tmp_path: Path) -> None:
    tool = _tool(tmp_path)
    await tool.execute(
        ToolRequest(operation="write", arguments={"path": "x.txt", "content": "alpha"})
    )
    await tool.execute(
        ToolRequest(operation="append", arguments={"path": "x.txt", "content": " beta"})
    )
    read = await tool.execute(ToolRequest(operation="read", arguments={"path": "x.txt"}))
    assert read.output == "alpha beta"
    listing = await tool.execute(ToolRequest(operation="list", arguments={"path": "."}))
    assert "x.txt" in listing.output
    search = await tool.execute(
        ToolRequest(operation="search", arguments={"path": ".", "term": "beta"})
    )
    assert search.output


async def test_sandbox_blocks_traversal(tmp_path: Path) -> None:
    tool = _tool(tmp_path)
    with pytest.raises(AuthorizationError):
        await tool.execute(ToolRequest(operation="read", arguments={"path": "../secret.txt"}))


async def test_validate_rejects_bad_requests(tmp_path: Path) -> None:
    tool = _tool(tmp_path)
    with pytest.raises(ValidationError):
        await tool.validate(ToolRequest(operation="chmod", arguments={"path": "x"}))
    with pytest.raises(ValidationError):
        await tool.validate(ToolRequest(operation="read", arguments={}))

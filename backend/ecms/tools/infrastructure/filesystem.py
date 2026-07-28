"""Sandboxed filesystem tool (SECTION 80/178).

Provides create/read/write/append/delete/list/exists/search operations, all
confined to a workspace sandbox. Every mutation returns the affected path as an
artifact.
"""

from __future__ import annotations

from ecms.shared.exceptions import ValidationError
from ecms.tools.domain.tool import ToolRequest, ToolResult
from ecms.tools.infrastructure.base import BaseTool
from ecms.tools.infrastructure.sandbox import WorkspaceSandbox

__all__ = ["FilesystemTool"]

_OPERATIONS = {"read", "write", "append", "delete", "list", "exists", "search"}


class FilesystemTool(BaseTool):
    """A filesystem tool confined to a workspace sandbox (SECTION 80)."""

    name = "filesystem"

    def __init__(self, sandbox: WorkspaceSandbox) -> None:
        """Initialize the tool with a workspace sandbox."""
        self._sandbox = sandbox

    async def validate(self, request: ToolRequest) -> None:
        """Ensure the operation is supported and a path is provided.

        Raises:
            ValidationError: If the operation is unknown or ``path`` is missing.
        """
        if request.operation not in _OPERATIONS:
            raise ValidationError(f"unsupported filesystem operation {request.operation!r}")
        if "path" not in request.arguments:
            raise ValidationError("filesystem operations require a 'path' argument")

    async def execute(self, request: ToolRequest) -> ToolResult:
        """Perform the filesystem operation within the sandbox."""
        arguments = request.arguments
        path = self._sandbox.resolve(str(arguments["path"]))
        operation = request.operation
        if operation in {"write", "append"}:
            path.parent.mkdir(parents=True, exist_ok=True)
            content = str(arguments.get("content", ""))
            if operation == "write":
                path.write_text(content, encoding="utf-8")
            else:
                with path.open("a", encoding="utf-8") as handle:
                    handle.write(content)
            return ToolResult(success=True, output=str(path), artifacts=[str(path)])
        if operation == "read":
            if not path.is_file():
                return ToolResult(success=False, error=f"not found: {arguments['path']}")
            return ToolResult(success=True, output=path.read_text(encoding="utf-8"))
        if operation == "delete":
            if not path.is_file():
                return ToolResult(success=False, error="not a file")
            path.unlink()
            return ToolResult(success=True, output=str(path))
        if operation == "exists":
            return ToolResult(success=True, output=path.exists())
        if operation == "list":
            if not path.is_dir():
                return ToolResult(success=False, error="not a directory")
            return ToolResult(success=True, output=sorted(child.name for child in path.iterdir()))
        term = str(arguments.get("term", ""))
        matches = [
            str(candidate)
            for candidate in path.rglob("*")
            if candidate.is_file()
            and term in candidate.read_text(encoding="utf-8", errors="ignore")
        ]
        return ToolResult(success=True, output=matches)

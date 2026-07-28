"""HTTP tool (SECTION 84/182).

Performs GET/POST/PUT/PATCH/DELETE requests through httpx. An httpx client may be
injected, which makes the tool fully testable offline via a mock transport.
"""

from __future__ import annotations

import httpx

from ecms.shared.exceptions import ValidationError
from ecms.tools.domain.tool import ToolRequest, ToolResult
from ecms.tools.infrastructure.base import BaseTool

__all__ = ["HttpTool"]

_METHODS = {"get", "post", "put", "patch", "delete"}


class HttpTool(BaseTool):
    """An HTTP tool for external requests (SECTION 84)."""

    name = "http"

    def __init__(self, *, client: httpx.AsyncClient | None = None) -> None:
        """Initialize the tool, optionally with an injected client for testing."""
        self._client = client

    async def validate(self, request: ToolRequest) -> None:
        """Ensure the method is supported and a URL is provided.

        Raises:
            ValidationError: If the method is unknown or ``url`` is missing.
        """
        if request.operation.lower() not in _METHODS:
            raise ValidationError(f"unsupported HTTP method {request.operation!r}")
        if "url" not in request.arguments:
            raise ValidationError("http operations require a 'url' argument")

    async def execute(self, request: ToolRequest) -> ToolResult:
        """Perform the HTTP request and return the status and body."""
        arguments = request.arguments
        client = self._client or httpx.AsyncClient()
        owns_client = self._client is None
        try:
            response = await client.request(
                request.operation.upper(),
                str(arguments["url"]),
                json=arguments.get("json"),
                headers=arguments.get("headers"),
            )
        finally:
            if owns_client:
                await client.aclose()
        return ToolResult(
            success=response.is_success,
            output={"status_code": response.status_code, "body": response.text},
        )

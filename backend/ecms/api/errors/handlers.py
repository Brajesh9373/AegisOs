"""API exception handlers (SECTION 77/82)."""

from __future__ import annotations

from typing import cast

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.responses import Response

from ecms.shared.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    EcmsError,
    NotFoundError,
    RateLimitedError,
    ValidationError,
)

__all__ = ["ecms_error_handler", "register_exception_handlers"]

_STATUS_BY_TYPE: dict[type[EcmsError], int] = {
    ValidationError: 422,
    AuthenticationError: 401,
    AuthorizationError: 403,
    NotFoundError: 404,
    ConflictError: 409,
    RateLimitedError: 429,
}


async def ecms_error_handler(_request: Request, exc: Exception) -> Response:
    """Render an :class:`EcmsError` as a JSON problem response."""
    error = cast("EcmsError", exc)
    status = _STATUS_BY_TYPE.get(type(error), 400)
    return JSONResponse(status_code=status, content=error.to_dict())


def register_exception_handlers(app: FastAPI) -> None:
    """Register the platform exception handlers on the application."""
    app.add_exception_handler(EcmsError, ecms_error_handler)

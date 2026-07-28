"""FastAPI dependency providers (SECTION 69/105)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from fastapi import Depends, Request

from ecms.auth import Identity, extract_bearer_token
from ecms.sdk import EcmsSDK
from ecms.shared.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from ecms.shared.exceptions import AuthenticationError

__all__ = ["Pagination", "get_pagination", "get_sdk", "require_identity"]


def get_sdk(request: Request) -> EcmsSDK:
    """Return the SDK bound to the application state."""
    return cast("EcmsSDK", request.app.state.sdk)


def require_identity(request: Request, sdk: EcmsSDK = Depends(get_sdk)) -> Identity:
    """Return the authenticated identity, raising 401 when absent or invalid."""
    token = extract_bearer_token(request.headers.get("Authorization"))
    if token is None:
        raise AuthenticationError("missing bearer token")
    return sdk.authentication.verify(token)


@dataclass(frozen=True)
class Pagination:
    """Validated pagination parameters."""

    page: int
    size: int

    @property
    def offset(self) -> int:
        """Return the zero-based offset for the page."""
        return (self.page - 1) * self.size


def get_pagination(page: int = 1, size: int = DEFAULT_PAGE_SIZE) -> Pagination:
    """Return validated pagination parameters (SECTION 82)."""
    return Pagination(page=max(page, 1), size=min(max(size, 1), MAX_PAGE_SIZE))

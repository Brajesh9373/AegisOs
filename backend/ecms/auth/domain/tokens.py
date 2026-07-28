"""Token models (SECTION 63/100)."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import Field

from ecms.auth.domain.identity import PrincipalType
from ecms.shared.models.base import DomainModel

__all__ = ["TokenClaims", "TokenPair", "TokenType"]


class TokenType(StrEnum):
    """The purpose of an issued token."""

    ACCESS = "access"
    REFRESH = "refresh"
    SERVICE = "service"
    SESSION = "session"


class TokenClaims(DomainModel):
    """Claims carried by a signed token."""

    subject: str
    token_type: TokenType
    principal_type: PrincipalType = PrincipalType.USER
    roles: list[str] = Field(default_factory=list)
    scopes: list[str] = Field(default_factory=list)
    tenant_id: str | None = None
    issued_at: datetime
    expires_at: datetime
    jti: str
    issuer: str = "ecms"
    audience: str = "ecms"


class TokenPair(DomainModel):
    """A freshly-issued access and refresh token pair."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"  # noqa: S105
    expires_in: int

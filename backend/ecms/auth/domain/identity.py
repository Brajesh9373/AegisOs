"""Identity and principal models (SECTION 100)."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from ecms.shared.models.base import DomainModel

__all__ = ["Identity", "PrincipalType"]


class PrincipalType(StrEnum):
    """The kind of authenticated principal."""

    USER = "user"
    SERVICE = "service"


class Identity(DomainModel):
    """An authenticated principal with roles and scopes (SECTION 100)."""

    subject: str
    principal_type: PrincipalType = PrincipalType.USER
    roles: list[str] = Field(default_factory=list)
    scopes: list[str] = Field(default_factory=list)
    tenant_id: str | None = None

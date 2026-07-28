"""Authorization domain models (SECTION 64/101)."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import Field

from ecms.shared.ids import new_id
from ecms.shared.models.base import DomainModel

__all__ = ["AccessDecision", "AccessRequest", "Policy", "PolicyEffect", "Role"]


def _policy_id() -> str:
    return new_id("policy")


class PolicyEffect(StrEnum):
    """Effect of an authorization policy."""

    ALLOW = "allow"
    DENY = "deny"


class Role(DomainModel):
    """A named role granting a set of ``resource:action`` permissions (SECTION 64)."""

    name: str
    permissions: list[str] = Field(default_factory=list)


class Policy(DomainModel):
    """An ABAC-ready authorization policy (SECTION 64/101)."""

    policy_id: str = Field(default_factory=_policy_id)
    effect: PolicyEffect
    resource: str
    action: str
    roles: list[str] = Field(default_factory=list)
    subjects: list[str] = Field(default_factory=list)
    conditions: dict[str, Any] = Field(default_factory=dict)


class AccessRequest(DomainModel):
    """A request to perform an action on a resource (SECTION 64)."""

    subject: str
    roles: list[str] = Field(default_factory=list)
    resource: str
    action: str
    attributes: dict[str, Any] = Field(default_factory=dict)


class AccessDecision(DomainModel):
    """The outcome of an authorization evaluation (SECTION 64)."""

    allowed: bool
    reason: str
    matched_policy: str | None = None

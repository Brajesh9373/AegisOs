"""Authorization port (SECTION 64)."""

from __future__ import annotations

from typing import Protocol

from ecms.auth.domain.authorization import AccessDecision, AccessRequest, Policy, Role
from ecms.auth.domain.identity import Identity
from ecms.shared.models.base import SecurityPolicy

__all__ = ["AuthorizationService"]


class AuthorizationService(Protocol):
    """Authorization service (SECTION 64).

    Operations:
        authorize: Evaluate an access request into a decision.
        grant: Grant a permission to a role (RBAC).
        deny: Add an explicit deny policy for a resource/action.
        check: Return whether a subject with roles may perform an action.
        roles: Return the registered roles.
        permissions: Return the permissions granted to a role.
        policies: Return the registered policies.
        knowledge_access: Return whether an identity may access a knowledge object.
    """

    def authorize(self, request: AccessRequest) -> AccessDecision: ...
    def grant(self, role_name: str, permission: str) -> None: ...
    def deny(
        self,
        resource: str,
        action: str,
        *,
        roles: list[str] | None = None,
        subjects: list[str] | None = None,
    ) -> Policy: ...
    def check(self, *, subject: str, roles: list[str], resource: str, action: str) -> bool: ...
    def roles(self) -> list[Role]: ...
    def permissions(self, role_name: str) -> list[str]: ...
    def policies(self) -> list[Policy]: ...
    def knowledge_access(self, identity: Identity, policy: SecurityPolicy) -> bool: ...

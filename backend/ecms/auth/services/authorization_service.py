"""RBAC + ABAC-ready policy authorization service (SECTION 64/101)."""

from __future__ import annotations

from collections.abc import Callable

from ecms.auth.domain.authorization import (
    AccessDecision,
    AccessRequest,
    Policy,
    PolicyEffect,
    Role,
)
from ecms.auth.domain.identity import Identity
from ecms.shared.enums import SecurityClassification
from ecms.shared.models.base import SecurityPolicy

__all__ = ["PolicyAuthorizationService"]

AuditHook = Callable[[AccessRequest, AccessDecision], None]


class PolicyAuthorizationService:
    """Evaluates access with role-based grants and allow/deny policies (SECTION 64).

    Evaluation order: explicit ``DENY`` policies win, then explicit ``ALLOW`` policies,
    then role-based permissions; otherwise access is denied (least privilege).
    """

    def __init__(self, *, audit_hook: AuditHook | None = None) -> None:
        """Initialize with an optional audit hook invoked on every decision."""
        self._roles: dict[str, Role] = {}
        self._policies: list[Policy] = []
        self._permissions: set[str] = set()
        self._audit_hook = audit_hook

    def register_role(self, role: Role) -> None:
        """Register a role and its permissions."""
        self._roles[role.name] = role
        self._permissions.update(role.permissions)

    def grant(self, role_name: str, permission: str) -> None:
        """Grant a ``resource:action`` permission to a role, creating it if needed."""
        self._permissions.add(permission)
        role = self._roles.get(role_name)
        if role is None:
            self._roles[role_name] = Role(name=role_name, permissions=[permission])
        elif permission not in role.permissions:
            role.permissions.append(permission)

    def allow(
        self,
        resource: str,
        action: str,
        *,
        roles: list[str] | None = None,
        subjects: list[str] | None = None,
        conditions: dict[str, object] | None = None,
    ) -> Policy:
        """Add an explicit allow policy (supports ABAC conditions)."""
        policy = Policy(
            effect=PolicyEffect.ALLOW,
            resource=resource,
            action=action,
            roles=roles or [],
            subjects=subjects or [],
            conditions=conditions or {},
        )
        self._policies.append(policy)
        return policy

    def deny(
        self,
        resource: str,
        action: str,
        *,
        roles: list[str] | None = None,
        subjects: list[str] | None = None,
    ) -> Policy:
        """Add an explicit deny policy for a resource/action."""
        policy = Policy(
            effect=PolicyEffect.DENY,
            resource=resource,
            action=action,
            roles=roles or [],
            subjects=subjects or [],
        )
        self._policies.append(policy)
        return policy

    def authorize(self, request: AccessRequest) -> AccessDecision:
        """Evaluate an access request into a decision, invoking the audit hook."""
        decision = self._evaluate(request)
        if self._audit_hook is not None:
            self._audit_hook(request, decision)
        return decision

    def check(self, *, subject: str, roles: list[str], resource: str, action: str) -> bool:
        """Return whether a subject with the given roles may perform an action."""
        request = AccessRequest(subject=subject, roles=roles, resource=resource, action=action)
        return self.authorize(request).allowed

    def roles(self) -> list[Role]:
        """Return the registered roles."""
        return list(self._roles.values())

    def permissions(self, role_name: str) -> list[str]:
        """Return the permissions granted to a role."""
        role = self._roles.get(role_name)
        return list(role.permissions) if role is not None else []

    def policies(self) -> list[Policy]:
        """Return the registered policies."""
        return list(self._policies)

    def knowledge_access(self, identity: Identity, policy: SecurityPolicy) -> bool:
        """Return whether an identity may access a knowledge object (SECTION 9/79)."""
        if identity.subject in policy.allowed_principals:
            return True
        if any(role in policy.allowed_roles for role in identity.roles):
            return True
        return policy.classification is SecurityClassification.PUBLIC

    def _evaluate(self, request: AccessRequest) -> AccessDecision:
        for policy in self._policies:
            if policy.effect is PolicyEffect.DENY and self._matches(policy, request):
                return AccessDecision(
                    allowed=False,
                    reason=f"denied by policy {policy.policy_id}",
                    matched_policy=policy.policy_id,
                )
        for policy in self._policies:
            if policy.effect is PolicyEffect.ALLOW and self._matches(policy, request):
                return AccessDecision(
                    allowed=True,
                    reason=f"allowed by policy {policy.policy_id}",
                    matched_policy=policy.policy_id,
                )
        required = f"{request.resource}:{request.action}"
        wildcard_action = f"{request.resource}:*"
        for role_name in request.roles:
            role = self._roles.get(role_name)
            if role is None:
                continue
            if (
                required in role.permissions
                or wildcard_action in role.permissions
                or "*:*" in role.permissions
            ):
                return AccessDecision(allowed=True, reason=f"granted by role {role_name}")
        return AccessDecision(allowed=False, reason="no matching grant (default deny)")

    def _matches(self, policy: Policy, request: AccessRequest) -> bool:
        if policy.resource not in ("*", request.resource):
            return False
        if policy.action not in ("*", request.action):
            return False
        if policy.roles and not any(role in policy.roles for role in request.roles):
            return False
        if policy.subjects and request.subject not in policy.subjects:
            return False
        return all(request.attributes.get(key) == value for key, value in policy.conditions.items())

"""Discovery identity resolution and non-disclosing access-scoped lookups.

Discovery sessions are tenant-owned state.  This module is deliberately kept at
that REST boundary so route handlers and service calls cannot accidentally use
a client-supplied user, organization, session, or project identifier as an
authority decision.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, NoReturn

from fastapi import HTTPException, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ecms.api.dependencies.providers import get_sdk
from ecms.auth import Identity
from ecms.configuration.schemas.settings import Profile, get_settings
from ecms.persistence.database.rest_session import db_session
from ecms.shared.exceptions import AuthenticationError

__all__ = [
    "DiscoveryIdentity",
    "load_discovery_project",
    "load_discovery_session",
    "resolve_discovery_identity",
]


@dataclass(frozen=True)
class DiscoveryIdentity:
    """A discovery actor resolved to durable platform identifiers only."""

    user_id: str
    organization_id: str
    roles: tuple[str, ...]
    authentication_method: str


def _authentication_error() -> NoReturn:
    """Reject authentication without exposing token or tenancy details."""
    raise HTTPException(
        status_code=401,
        detail={"error": "AUTH-401", "message": "Authentication required"},
    )


def _identity_authority_unavailable() -> NoReturn:
    """Fail closed when production cannot verify tenant membership/trust."""
    raise HTTPException(
        status_code=503,
        detail={
            "error": "DISCOVERY-IDENTITY-UNAVAILABLE",
            "message": "Discovery identity authority is unavailable",
        },
    )


def _not_found(resource: str) -> NoReturn:
    """Return the same result for missing and inaccessible discovery resources."""
    raise HTTPException(
        status_code=404,
        detail={"error": "NOT-FOUND", "message": f"{resource} not found"},
    )


def _bearer_token(request: Request) -> str:
    authorization = request.headers.get("Authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        _authentication_error()
    return token.strip()


def _row_to_dict(row: Any) -> dict[str, Any]:
    """Normalize SQLAlchemy row mapping keys across PostgreSQL and SQLite."""
    return {key.lower(): value for key, value in row._mapping.items()}


def _ui_session_expired(value: Any) -> bool:
    """Return whether a legacy UI-session expiry value is absent, invalid, or elapsed."""
    if value is None:
        return True
    raw = str(value).strip()
    if not raw:
        return True
    try:
        timestamp = int(raw)
    except ValueError:
        try:
            expiry = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return True
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=UTC)
        return expiry <= datetime.now(UTC)
    if timestamp < 10_000_000_000:
        return timestamp <= int(datetime.now(UTC).timestamp())
    return timestamp <= int(datetime.now(UTC).timestamp() * 1000)


async def _trusted_organization_id(
    session: AsyncSession,
    requested_organization_id: str | None = None,
) -> str:
    """Resolve a persisted organization matching the verified tenant claim.

    This checks resource tenancy, not membership. The current schema has no
    canonical tenant-membership or trusted-server authority, so production must
    reject before reaching this helper. Development/test compatibility may use
    the one installed organization only when it is unambiguous.
    """
    if requested_organization_id:
        row = (
            await session.execute(
                text("SELECT id FROM organization WHERE id = :id"),
                {"id": requested_organization_id},
            )
        ).first()
        if row is None:
            _authentication_error()
        return str(row[0])

    rows = (
        await session.execute(text("SELECT id FROM organization ORDER BY id LIMIT 2"))
    ).fetchall()
    if len(rows) != 1:
        _authentication_error()
    return str(rows[0][0])


def _is_tenant_admin(identity: DiscoveryIdentity) -> bool:
    """Return whether a persisted platform role may administer tenant resources."""
    roles = {role.strip().lower() for role in identity.roles}
    return bool({"admin", "administrator", "org admin", "super admin", "superadmin"} & roles)


async def _active_user(
    session: AsyncSession,
    user_id: str,
) -> tuple[str, tuple[str, ...]]:
    """Load an active user by immutable users.id rather than mutable email."""
    row = (
        await session.execute(
            text("SELECT id, role, active FROM users WHERE id = :id"),
            {"id": user_id},
        )
    ).first()
    if row is None:
        _authentication_error()
    user = _row_to_dict(row)
    if not bool(user.get("active")):
        _authentication_error()
    role = user.get("role")
    return str(user["id"]), (str(role),) if role else ()


async def _identity_from_jwt(identity: Identity) -> DiscoveryIdentity:
    """Turn a cryptographically verified JWT into a trusted discovery identity."""
    if not identity.subject or not identity.tenant_id:
        _authentication_error()
    async with db_session() as session:
        user_id, roles = await _active_user(session, identity.subject)
        organization_id = await _trusted_organization_id(session, identity.tenant_id)
    return DiscoveryIdentity(
        user_id=user_id,
        organization_id=organization_id,
        roles=roles,
        authentication_method="jwt",
    )


async def _identity_from_ui_session(token: str) -> DiscoveryIdentity:
    """Resolve a development/test legacy UI session with its expiry enforced."""
    async with db_session() as session:
        row = (
            await session.execute(
                text(
                    "SELECT auth_sessions.userid AS user_id, auth_sessions.expiresat AS expires_at, "
                    "users.id AS resolved_user_id, users.role AS role, users.active AS active "
                    "FROM auth_sessions JOIN users ON users.id = auth_sessions.userid "
                    "WHERE auth_sessions.token = :token"
                ),
                {"token": token},
            )
        ).first()
        if row is None:
            _authentication_error()
        resolved = _row_to_dict(row)
        if _ui_session_expired(resolved.get("expires_at")) or not bool(resolved.get("active")):
            _authentication_error()
        # The join and equality check defend against a malformed legacy session
        # row being interpreted as a different user.
        if resolved.get("user_id") != resolved.get("resolved_user_id"):
            _authentication_error()
        organization_id = await _trusted_organization_id(session)
    role = resolved.get("role")
    return DiscoveryIdentity(
        user_id=str(resolved["resolved_user_id"]),
        organization_id=organization_id,
        roles=(str(role),) if role else (),
        authentication_method="ui-session",
    )


async def _check_membership(
    session: AsyncSession,
    user_id: str,
    organization_id: str,
) -> tuple[str, tuple[str, ...]]:
    """Verify user is an active member of the organization.

    Returns (member_id, roles) on success. Fails closed if no valid membership.
    """
    # Check if user is linked to an active organization member in this org
    row = (
        await session.execute(
            text(
                "SELECT om.id, om.role FROM organization_members om "
                "WHERE om.user_id = :user_id AND om.status = 'active' "
                "LIMIT 1"
            ),
            {"user_id": user_id},
        )
    ).first()
    if row is None:
        _authentication_error()
    member_id = str(row[0])
    role = str(row[1]) if row[1] else ""
    return member_id, (role,) if role else ()


async def resolve_discovery_identity(request: Request) -> DiscoveryIdentity:
    """Resolve the caller before a discovery operation.

    Production uses server-trusted membership authority: a verified JWT or UI
    session must map to an active organization member in the claimed tenant.
    Development/testing supports legacy UI sessions with the fallback checks.
    """
    token = _bearer_token(request)

    # Try JWT first (primary path in all environments)
    verified_identity: Identity | None = None
    try:
        verified_identity = get_sdk(request).authentication.verify(token)
    except AuthenticationError:
        pass
    except Exception:
        pass

    if verified_identity is not None:
        if not verified_identity.subject or not verified_identity.tenant_id:
            _authentication_error()
        async with db_session() as session:
            # Verify user exists and is active
            user_id, user_roles = await _active_user(session, verified_identity.subject)
            # Resolve organization from tenant claim
            organization_id = await _trusted_organization_id(session, verified_identity.tenant_id)
            # Check membership - this is the key production check
            member_id, member_roles = await _check_membership(session, user_id, organization_id)
        return DiscoveryIdentity(
            user_id=member_id,
            organization_id=organization_id,
            roles=member_roles or user_roles,
            authentication_method="jwt",
        )

    # Fallback to UI session (development/testing only)
    profile = get_settings().environment
    if profile not in {Profile.DEVELOPMENT, Profile.TESTING}:
        _identity_authority_unavailable()
    return await _identity_from_ui_session(token)


async def load_discovery_session(
    session: AsyncSession,
    session_id: str,
    identity: DiscoveryIdentity,
    *,
    for_update: bool = False,
) -> dict[str, Any]:
    """Load one discovery session only when its owner and tenant both match.

    A linked project is also checked to defend against stale or corrupted links.
    Missing and unauthorized sessions intentionally share the same 404 response.
    """
    lock_clause = ""
    if for_update and session.get_bind().dialect.name != "sqlite":
        lock_clause = " FOR UPDATE"
    row = (
        await session.execute(
            text(
                "SELECT discovery_sessions.* FROM discovery_sessions "
                "LEFT JOIN business_projects ON business_projects.id = discovery_sessions.project_id "
                "WHERE discovery_sessions.id = :session_id "
                "AND discovery_sessions.organization_id = :organization_id "
                "AND (:is_admin = 1 OR discovery_sessions.owner_id = :user_id) "
                "AND (discovery_sessions.project_id IS NULL OR ("
                "business_projects.organization_id = :organization_id "
                "AND (:is_admin = 1 OR business_projects.ownerid = :user_id)))" + lock_clause
            ),
            {
                "session_id": session_id,
                "user_id": identity.user_id,
                "organization_id": identity.organization_id,
                "is_admin": int(_is_tenant_admin(identity)),
            },
        )
    ).first()
    if row is None:
        _not_found("Discovery session")
    return _row_to_dict(row)


async def load_discovery_project(
    session: AsyncSession,
    project_id: str,
    identity: DiscoveryIdentity,
) -> dict[str, Any]:
    """Load one project only when its persisted owner and tenant both match."""
    row = (
        await session.execute(
            text(
                "SELECT * FROM business_projects WHERE id = :project_id "
                "AND organization_id = :organization_id "
                "AND (:is_admin = 1 OR ownerid = :user_id)"
            ),
            {
                "project_id": project_id,
                "user_id": identity.user_id,
                "organization_id": identity.organization_id,
                "is_admin": int(_is_tenant_admin(identity)),
            },
        )
    ).first()
    if row is None:
        _not_found("Project")
    return _row_to_dict(row)

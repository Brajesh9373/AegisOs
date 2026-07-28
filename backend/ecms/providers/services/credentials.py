"""Credential manager (SECTION 120).

Owns credential storage, rotation, expiration and revocation. Credentials are
never hardcoded; production deployments back this with a secrets manager or vault.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime

from ecms.shared.exceptions import NotFoundError
from ecms.shared.time import utcnow

__all__ = ["Credential", "CredentialManager"]


@dataclass(frozen=True, slots=True)
class Credential:
    """A stored credential with lifecycle metadata (SECTION 120)."""

    key: str
    value: str
    created_at: datetime
    rotated_at: datetime | None = None
    revoked: bool = False


class CredentialManager:
    """Manages credential storage, rotation and revocation (SECTION 120)."""

    def __init__(self) -> None:
        """Initialize with no stored credentials."""
        self._credentials: dict[str, Credential] = {}

    async def store(self, key: str, value: str) -> None:
        """Store a credential under a key."""
        self._credentials[key] = Credential(key=key, value=value, created_at=utcnow())

    async def get(self, key: str) -> str | None:
        """Return a credential's value, or ``None`` if absent or revoked."""
        credential = self._credentials.get(key)
        if credential is None or credential.revoked:
            return None
        return credential.value

    async def rotate(self, key: str, new_value: str) -> None:
        """Rotate a credential's value.

        Raises:
            NotFoundError: If no credential exists under ``key``.
        """
        credential = self._require(key)
        self._credentials[key] = replace(credential, value=new_value, rotated_at=utcnow())

    async def revoke(self, key: str) -> None:
        """Revoke a credential so it can no longer be read.

        Raises:
            NotFoundError: If no credential exists under ``key``.
        """
        credential = self._require(key)
        self._credentials[key] = replace(credential, revoked=True)

    def _require(self, key: str) -> Credential:
        credential = self._credentials.get(key)
        if credential is None:
            raise NotFoundError(f"credential {key!r} not found")
        return credential

"""API key generation and verification (SECTION 100)."""

from __future__ import annotations

import hashlib
import secrets

from ecms.shared.security import constant_time_compare

__all__ = ["ApiKeyManager"]


class ApiKeyManager:
    """Generates API keys and verifies them against stored hashes."""

    def __init__(self, prefix: str = "ecms") -> None:
        """Initialize the manager with an API-key prefix."""
        self._prefix = prefix

    def generate(self) -> tuple[str, str]:
        """Return a new ``(api_key, hash)`` pair. Only the hash should be stored."""
        key = f"{self._prefix}_{secrets.token_urlsafe(32)}"
        return key, self._hash(key)

    def verify(self, key: str, hashed: str) -> bool:
        """Return whether an API key matches a stored hash."""
        return constant_time_compare(self._hash(key), hashed)

    def _hash(self, key: str) -> str:
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

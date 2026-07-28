"""Bcrypt password hasher (SECTION 100)."""

from __future__ import annotations

import bcrypt

__all__ = ["BcryptPasswordHasher"]


class BcryptPasswordHasher:
    """Hashes and verifies passwords using bcrypt."""

    def hash(self, password: str) -> str:
        """Return a salted bcrypt hash of the password."""
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def verify(self, password: str, hashed: str) -> bool:
        """Return whether the password matches the bcrypt hash."""
        try:
            return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
        except ValueError:
            return False

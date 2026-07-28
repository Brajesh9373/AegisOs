"""Bearer token extraction (SECTION 100)."""

from __future__ import annotations

__all__ = ["extract_bearer_token"]


def extract_bearer_token(authorization: str | None) -> str | None:
    """Extract the token from an ``Authorization: Bearer <token>`` header value.

    Args:
        authorization: The raw ``Authorization`` header value, or ``None``.

    Returns:
        The bearer token, or ``None`` if the header is missing or not a bearer scheme.
    """
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token

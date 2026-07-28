"""Root, version and identity routes (SECTION 69)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ecms import __version__
from ecms.api.dependencies.providers import require_identity
from ecms.auth import Identity

router = APIRouter(tags=["system"])


@router.get("/")
async def root() -> dict[str, str]:
    """Return platform information."""
    return {"name": "Enterprise Cognitive Memory System", "version": __version__}


@router.get("/version")
async def version() -> dict[str, str]:
    """Return the platform version."""
    return {"version": __version__}


@router.get("/whoami")
async def whoami(identity: Identity = Depends(require_identity)) -> dict[str, object]:
    """Return the authenticated identity (requires a bearer token)."""
    return {"subject": identity.subject, "roles": identity.roles}

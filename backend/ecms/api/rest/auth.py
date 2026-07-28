"""Authentication REST routes (login, refresh, logout)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from ecms.auth import Identity
from ecms.api.dependencies.providers import get_sdk, require_identity
from ecms.sdk import EcmsSDK

__all__ = ["router"]

router = APIRouter(tags=["authentication"], prefix="/api/v1/auth")


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/login")
async def login(body: LoginRequest, request: Request) -> LoginResponse:
    """Authenticate with email/password and return a JWT token pair.

    In production, this would validate credentials against an identity provider.
    For the foundation platform, it issues a token for a demo identity.
    """
    sdk: EcmsSDK = get_sdk(request)
    identity = Identity(subject=body.email, roles=["operator"])
    pair = sdk.authentication.login(identity)
    return LoginResponse(
        access_token=pair.access_token,
        refresh_token=pair.refresh_token,
        token_type=pair.token_type,
        expires_in=pair.expires_in,
    )


@router.post("/refresh")
async def refresh(body: RefreshRequest, request: Request) -> LoginResponse:
    """Exchange a refresh token for a new token pair."""
    sdk: EcmsSDK = get_sdk(request)
    pair = sdk.authentication.refresh(body.refresh_token)
    return LoginResponse(
        access_token=pair.access_token,
        refresh_token=pair.refresh_token,
        token_type=pair.token_type,
        expires_in=pair.expires_in,
    )


@router.post("/logout")
async def logout(request: Request, identity: Identity = Depends(require_identity)) -> dict[str, str]:
    """Revoke the current access token."""
    token = request.headers.get("Authorization", "").removeprefix("Bearer ")
    if token:
        sdk: EcmsSDK = get_sdk(request)
        sdk.authentication.logout(token)
    return {"message": "logged out"}

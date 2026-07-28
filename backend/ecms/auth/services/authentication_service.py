"""JWT-based authentication service (SECTION 63/100)."""

from __future__ import annotations

from datetime import timedelta

from ecms.auth.domain.identity import Identity
from ecms.auth.domain.tokens import TokenClaims, TokenPair, TokenType
from ecms.auth.interfaces.service import TokenCodec
from ecms.shared.exceptions import AuthenticationError
from ecms.shared.ids import new_uuid
from ecms.shared.time import utcnow

__all__ = ["JwtAuthenticationService"]


class JwtAuthenticationService:
    """Issues, verifies, refreshes and revokes JWT tokens (SECTION 63)."""

    def __init__(
        self,
        codec: TokenCodec,
        *,
        access_ttl_seconds: int = 900,
        refresh_ttl_seconds: int = 86_400,
    ) -> None:
        """Initialize the service with a token codec and token lifetimes."""
        self._codec = codec
        self._access_ttl = access_ttl_seconds
        self._refresh_ttl = refresh_ttl_seconds
        self._revoked: set[str] = set()

    def issue_token(
        self,
        identity: Identity,
        token_type: TokenType = TokenType.ACCESS,
        ttl: int | None = None,
    ) -> str:
        """Issue a single signed token of the given type for an identity."""
        now = utcnow()
        lifetime = ttl if ttl is not None else self._access_ttl
        claims = TokenClaims(
            subject=identity.subject,
            token_type=token_type,
            principal_type=identity.principal_type,
            roles=identity.roles,
            scopes=identity.scopes,
            tenant_id=identity.tenant_id,
            issued_at=now,
            expires_at=now + timedelta(seconds=lifetime),
            jti=new_uuid(),
        )
        return self._codec.encode(claims)

    def login(self, identity: Identity) -> TokenPair:
        """Mint an access and refresh token pair for an authenticated identity."""
        access = self.issue_token(identity, TokenType.ACCESS, self._access_ttl)
        refresh = self.issue_token(identity, TokenType.REFRESH, self._refresh_ttl)
        return TokenPair(access_token=access, refresh_token=refresh, expires_in=self._access_ttl)

    def verify(self, token: str) -> Identity:
        """Decode and verify a token, returning the identity.

        Raises:
            AuthenticationError: If the token is invalid or revoked.
        """
        claims = self._codec.decode(token)
        if claims.jti in self._revoked:
            raise AuthenticationError("token has been revoked")
        return Identity(
            subject=claims.subject,
            principal_type=claims.principal_type,
            roles=claims.roles,
            scopes=claims.scopes,
            tenant_id=claims.tenant_id,
        )

    def validate(self, token: str) -> bool:
        """Return whether a token is currently valid."""
        try:
            self.verify(token)
        except AuthenticationError:
            return False
        return True

    def refresh(self, refresh_token: str) -> TokenPair:
        """Exchange a valid refresh token for a new token pair.

        Raises:
            AuthenticationError: If the token is not a valid, unrevoked refresh token.
        """
        claims = self._codec.decode(refresh_token)
        if claims.token_type is not TokenType.REFRESH:
            raise AuthenticationError("not a refresh token")
        if claims.jti in self._revoked:
            raise AuthenticationError("token has been revoked")
        self._revoked.add(claims.jti)
        identity = Identity(
            subject=claims.subject,
            principal_type=claims.principal_type,
            roles=claims.roles,
            scopes=claims.scopes,
            tenant_id=claims.tenant_id,
        )
        return self.login(identity)

    def revoke(self, token: str) -> None:
        """Revoke a token by its identifier, ignoring invalid tokens."""
        try:
            claims = self._codec.decode(token)
        except AuthenticationError:
            return
        self._revoked.add(claims.jti)

    def logout(self, token: str) -> None:
        """Revoke a token as part of logout."""
        self.revoke(token)

    def rotate_keys(self) -> None:
        """Rotate the signing keys used to issue new tokens."""
        self._codec.rotate()

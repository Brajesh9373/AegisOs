"""JWT token codec with rotating symmetric signing keys (SECTION 100)."""

from __future__ import annotations

from datetime import UTC, datetime

import jwt

from ecms.auth.domain.identity import PrincipalType
from ecms.auth.domain.tokens import TokenClaims, TokenType
from ecms.shared.exceptions import AuthenticationError
from ecms.shared.ids import new_uuid

__all__ = ["JwtTokenCodec"]


class JwtTokenCodec:
    """Encodes and decodes JWTs. Rotated keys remain valid for verification."""

    def __init__(
        self,
        *,
        secret: str | None = None,
        issuer: str = "ecms",
        audience: str = "ecms",
        algorithm: str = "HS256",
    ) -> None:
        """Initialize the codec and register an initial signing key."""
        self._issuer = issuer
        self._audience = audience
        self._algorithm = algorithm
        self._keys: dict[str, str] = {}
        self._current_kid = self.rotate(secret)

    def rotate(self, secret: str | None = None) -> str:
        """Rotate to a new signing key and return its id. Old keys still verify."""
        kid = new_uuid()
        self._keys[kid] = secret or new_uuid()
        self._current_kid = kid
        return kid

    def encode(self, claims: TokenClaims) -> str:
        """Sign token claims into a compact JWT."""
        payload = {
            "sub": claims.subject,
            "type": claims.token_type.value,
            "ptype": claims.principal_type.value,
            "roles": claims.roles,
            "scopes": claims.scopes,
            "tenant": claims.tenant_id,
            "iat": int(claims.issued_at.timestamp()),
            "exp": int(claims.expires_at.timestamp()),
            "jti": claims.jti,
            "iss": self._issuer,
            "aud": self._audience,
        }
        return jwt.encode(
            payload,
            self._keys[self._current_kid],
            algorithm=self._algorithm,
            headers={"kid": self._current_kid},
        )

    def decode(self, token: str) -> TokenClaims:
        """Verify and decode a JWT into claims.

        Raises:
            AuthenticationError: If the token is malformed, expired, or signed with an
                unknown key.
        """
        try:
            kid = jwt.get_unverified_header(token).get("kid")
        except jwt.PyJWTError as exc:
            raise AuthenticationError(f"invalid token header: {exc}") from exc
        if not isinstance(kid, str):
            raise AuthenticationError("missing signing key id")
        secret = self._keys.get(kid)
        if secret is None:
            raise AuthenticationError("unknown signing key")
        try:
            payload = jwt.decode(
                token,
                secret,
                algorithms=[self._algorithm],
                audience=self._audience,
                issuer=self._issuer,
            )
        except jwt.PyJWTError as exc:
            raise AuthenticationError(f"invalid token: {exc}") from exc
        return TokenClaims(
            subject=payload["sub"],
            token_type=TokenType(payload["type"]),
            principal_type=PrincipalType(payload["ptype"]),
            roles=payload.get("roles", []),
            scopes=payload.get("scopes", []),
            tenant_id=payload.get("tenant"),
            issued_at=datetime.fromtimestamp(payload["iat"], tz=UTC),
            expires_at=datetime.fromtimestamp(payload["exp"], tz=UTC),
            jti=payload["jti"],
            issuer=payload["iss"],
            audience=payload["aud"],
        )

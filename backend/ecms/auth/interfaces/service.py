"""Authentication ports (SECTION 63/100)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ecms.auth.domain.identity import Identity
from ecms.auth.domain.tokens import TokenClaims, TokenPair, TokenType

__all__ = ["AuthenticationService", "PasswordHasher", "TokenCodec"]


@runtime_checkable
class PasswordHasher(Protocol):
    """Hashes and verifies passwords.

    Operations:
        hash: Return a salted hash of a plaintext password.
        verify: Return whether a plaintext password matches a hash.
    """

    def hash(self, password: str) -> str: ...
    def verify(self, password: str, hashed: str) -> bool: ...


@runtime_checkable
class TokenCodec(Protocol):
    """Encodes and decodes signed tokens, supporting key rotation.

    Operations:
        encode: Sign token claims and return a compact token.
        decode: Verify and decode a token into claims.
        rotate: Rotate the active signing key and return its id.
    """

    def encode(self, claims: TokenClaims) -> str: ...
    def decode(self, token: str) -> TokenClaims: ...
    def rotate(self, secret: str | None = None) -> str: ...


class AuthenticationService(Protocol):
    """Authentication service (SECTION 63).

    Operations:
        login: Mint an access and refresh token pair for an identity.
        logout: Revoke a token.
        refresh: Exchange a refresh token for a new token pair.
        validate: Return whether a token is currently valid.
        verify: Decode and verify a token into an identity.
        rotate_keys: Rotate the signing keys.
        issue_token: Issue a single token of a given type for an identity.
        revoke: Revoke a token by its identifier.
    """

    def login(self, identity: Identity) -> TokenPair: ...
    def logout(self, token: str) -> None: ...
    def refresh(self, refresh_token: str) -> TokenPair: ...
    def validate(self, token: str) -> bool: ...
    def verify(self, token: str) -> Identity: ...
    def rotate_keys(self) -> None: ...
    def issue_token(
        self,
        identity: Identity,
        token_type: TokenType = TokenType.ACCESS,
        ttl: int | None = None,
    ) -> str: ...
    def revoke(self, token: str) -> None: ...

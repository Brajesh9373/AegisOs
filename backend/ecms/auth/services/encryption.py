"""Encryption service (SECTION 218).

Provides AES-256-GCM authenticated encryption for credentials, secrets and PII.
Keys can be rotated; ciphertext is self-describing (nonce prepended) and base64
encoded for safe storage and transport.
"""

from __future__ import annotations

import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

__all__ = ["EncryptionService"]

_NONCE_BYTES = 12
_KEY_BITS = 256


class EncryptionService:
    """AES-256-GCM authenticated encryption with key rotation (SECTION 218)."""

    def __init__(self, key: bytes | None = None) -> None:
        """Initialize with a 256-bit key, generating one when none is given."""
        self._key = key or AESGCM.generate_key(bit_length=_KEY_BITS)
        self._aead = AESGCM(self._key)

    @staticmethod
    def generate_key() -> bytes:
        """Return a fresh random 256-bit key."""
        return AESGCM.generate_key(bit_length=_KEY_BITS)

    def encrypt(self, plaintext: str) -> str:
        """Encrypt plaintext, returning base64(nonce || ciphertext)."""
        nonce = os.urandom(_NONCE_BYTES)
        ciphertext = self._aead.encrypt(nonce, plaintext.encode("utf-8"), None)
        return base64.b64encode(nonce + ciphertext).decode("ascii")

    def decrypt(self, token: str) -> str:
        """Decrypt a token produced by :meth:`encrypt`."""
        raw = base64.b64decode(token)
        nonce, ciphertext = raw[:_NONCE_BYTES], raw[_NONCE_BYTES:]
        return self._aead.decrypt(nonce, ciphertext, None).decode("utf-8")

    def rotate_key(self) -> bytes:
        """Rotate to a new random key and return it."""
        self._key = AESGCM.generate_key(bit_length=_KEY_BITS)
        self._aead = AESGCM(self._key)
        return self._key

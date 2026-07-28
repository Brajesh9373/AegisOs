"""Secrets-manager adapters."""

from ecms.infrastructure.secrets.provider import EnvSecretsProvider, SecretsProvider

__all__ = ["EnvSecretsProvider", "SecretsProvider"]

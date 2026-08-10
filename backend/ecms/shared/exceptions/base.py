"""Typed exception hierarchy for the ECMS platform (SECTION 77).

Every error raised by the platform derives from :class:`EcmsError`, carries a stable
machine-readable ``code`` and an optional structured ``details`` mapping, and can be
serialized for API error responses via :meth:`EcmsError.to_dict`.
"""

from __future__ import annotations

from typing import Any

__all__ = [
    "AuthenticationError",
    "AuthorizationError",
    "ConfigurationError",
    "ConflictError",
    "DependencyResolutionError",
    "EcmsError",
    "EventError",
    "NotFoundError",
    "PluginError",
    "RateLimitedError",
    "RepositoryError",
    "SerializationError",
    "ValidationError",
]


class EcmsError(Exception):
    """Base class for every error raised by the platform.

    Attributes:
        message: Human-readable error message.
        code: Stable, machine-readable error code.
        details: Optional structured context. Must never contain secrets or PII.
    """

    default_message: str = "An ECMS error occurred."
    default_code: str = "ecms_error"

    def __init__(
        self,
        message: str | None = None,
        *,
        code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the error with an optional message, code and details."""
        self.message = message or self.default_message
        self.code = code or self.default_code
        self.details: dict[str, Any] = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation for API error responses."""
        return {"error": self.code, "message": self.message, "details": self.details}


class ValidationError(EcmsError):
    """Raised when input fails validation."""

    default_message = "Validation failed."
    default_code = "validation_error"


class NotFoundError(EcmsError):
    """Raised when a requested resource does not exist."""

    default_message = "Resource not found."
    default_code = "not_found"


class ConflictError(EcmsError):
    """Raised when an operation conflicts with existing state."""

    default_message = "Conflicting state."
    default_code = "conflict"


class AuthenticationError(EcmsError):
    """Raised when authentication fails."""

    default_message = "Authentication failed."
    default_code = "authentication_error"


class AuthorizationError(EcmsError):
    """Raised when an authenticated principal lacks permission."""

    default_message = "Authorization denied."
    default_code = "authorization_error"


class ConfigurationError(EcmsError):
    """Raised when configuration is missing or invalid."""

    default_message = "Invalid configuration."
    default_code = "configuration_error"


class SerializationError(EcmsError):
    """Raised when serialization or deserialization fails."""

    default_message = "Serialization failed."
    default_code = "serialization_error"


class RepositoryError(EcmsError):
    """Raised when a repository operation fails."""

    default_message = "Repository operation failed."
    default_code = "repository_error"


class EventError(EcmsError):
    """Raised when publishing, routing, or handling an event fails."""

    default_message = "Event processing failed."
    default_code = "event_error"


class PluginError(EcmsError):
    """Raised when a plugin operation fails."""

    default_message = "Plugin operation failed."
    default_code = "plugin_error"


class RateLimitedError(EcmsError):
    """Raised when an operation is rejected due to rate limiting."""

    default_message = "Rate limit exceeded."
    default_code = "rate_limited"


class DependencyResolutionError(EcmsError):
    """Raised when the dependency-injection container cannot resolve a dependency."""

    default_message = "Dependency resolution failed."
    default_code = "dependency_resolution_error"


class LlmProviderError(EcmsError):
    """Raised when the LLM provider fails after retries / breaker."""

    default_message = "LLM provider error."
    default_code = "llm_provider_error"


class DiscoveryError(EcmsError):
    """Raised for discovery state-machine violations."""

    default_message = "Discovery operation failed."
    default_code = "discovery_error"


class DiscoveryConflictError(EcmsError):
    """Raised when a discovery transition conflicts with current stage."""

    default_message = "Discovery state conflict."
    default_code = "discovery_conflict"

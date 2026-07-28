"""Typed exception hierarchy (SECTION 77)."""

from ecms.shared.exceptions.base import (
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    ConflictError,
    DependencyResolutionError,
    EcmsError,
    EventError,
    NotFoundError,
    PluginError,
    RateLimitedError,
    RepositoryError,
    SerializationError,
    ValidationError,
)

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

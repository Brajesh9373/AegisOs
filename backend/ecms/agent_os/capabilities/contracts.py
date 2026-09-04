"""Host-mediated capability contracts for the Agent OS execution plane."""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import StrEnum
from typing import Any

from pydantic import Field, field_validator, model_validator

from ecms.plugins.infrastructure.base import BasePlugin
from ecms.shared.models.base import ImmutableModel

__all__ = [
    "CapabilityEffect",
    "CapabilityExecutionContext",
    "CapabilityExecutionResult",
    "CapabilityPlugin",
    "CapabilityPolicyError",
    "CapabilitySpec",
]


class CapabilityPolicyError(ValueError):
    """Raised when a capability contract permits an unsafe effect policy."""


class CapabilityEffect(StrEnum):
    """The host-controlled effect class of an allowlisted capability."""

    READ = "read"
    WRITE = "write"
    EXTERNAL = "external"


class CapabilitySpec(ImmutableModel):
    """Static policy for one named, versioned host capability adapter."""

    capability_id: str
    version: str
    effect: CapabilityEffect
    request_schema_ref: str
    result_schema_ref: str
    requires_approval: bool = False
    requires_idempotency_key: bool = False
    max_arguments_bytes: int = Field(default=16 * 1024, ge=1_024, le=256 * 1024)
    max_result_bytes: int = Field(default=32 * 1024, ge=1_024, le=512 * 1024)

    @field_validator("capability_id")
    @classmethod
    def validate_capability_id(cls, value: str) -> str:
        """Keep capability names stable and host-addressable."""
        if not isinstance(value, str) or not value.strip():
            raise ValueError("capability_id must be a non-empty string")
        normalized = value.strip()
        allowed_characters = "abcdefghijklmnopqrstuvwxyz0123456789._-"
        if any(character not in allowed_characters for character in normalized):
            raise ValueError("capability_id must use lowercase identifier characters")
        if not normalized[0].isalpha():
            raise ValueError("capability_id must start with a lowercase letter")
        return normalized

    @field_validator("version", "request_schema_ref", "result_schema_ref")
    @classmethod
    def validate_non_secret_refs(cls, value: str) -> str:
        """Require local, bounded contract references rather than arbitrary URLs."""
        if not isinstance(value, str) or not value.strip() or "\x00" in value:
            raise ValueError("capability contract references must be non-empty and NUL-free")
        normalized = value.strip()
        if "://" in normalized:
            raise ValueError("capability contract references must be local")
        return normalized

    @model_validator(mode="after")
    def require_safe_effect_policy(self) -> CapabilitySpec:
        """Make every non-read side effect explicitly approved and idempotent."""
        if self.effect in {CapabilityEffect.WRITE, CapabilityEffect.EXTERNAL}:
            if not self.requires_approval:
                raise CapabilityPolicyError("write and external capabilities require approval")
            if not self.requires_idempotency_key:
                raise CapabilityPolicyError(
                    "write and external capabilities require idempotency keys"
                )
        return self


class CapabilityExecutionContext(ImmutableModel):
    """Host-created correlation data supplied to an approved capability adapter."""

    organization_id: str = Field(min_length=1, max_length=128)
    run_id: str = Field(min_length=1, max_length=128)
    step_id: str = Field(min_length=1, max_length=128)
    worker_id: str = Field(min_length=1, max_length=128)
    profile_identity: str = Field(min_length=3, max_length=256)
    policy_revision: str = Field(min_length=1, max_length=128)

    @field_validator(
        "organization_id",
        "run_id",
        "step_id",
        "worker_id",
        "profile_identity",
        "policy_revision",
    )
    @classmethod
    def reject_control_bytes(cls, value: str) -> str:
        """Protect audit correlation fields from log/control-character injection."""
        if "\x00" in value or any(ord(character) < 32 for character in value):
            raise ValueError("capability context fields must not contain control characters")
        return value


class CapabilityExecutionResult(ImmutableModel):
    """Bounded, redacted data that may return to DSH as untrusted reference data."""

    result: dict[str, Any]
    audit_metadata: dict[str, str] = Field(default_factory=dict)

    @field_validator("result")
    @classmethod
    def validate_result(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject non-object result payloads before a host renders them back to DSH."""
        if not isinstance(value, dict):
            raise ValueError("capability result must be a JSON object")
        return value


class CapabilityPlugin(BasePlugin, ABC):
    """Lifecycle-managed host adapter for one explicitly allowlisted capability."""

    @property
    @abstractmethod
    def capability_spec(self) -> CapabilitySpec:
        """Return the immutable declared capability policy."""

    @abstractmethod
    async def execute(
        self,
        *,
        context: CapabilityExecutionContext,
        arguments: dict[str, Any],
    ) -> CapabilityExecutionResult:
        """Execute a broker-authorized action with no ambient DSH authority."""

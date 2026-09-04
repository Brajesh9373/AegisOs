"""Profile-neutral contracts for deployment-owned DSH profiles.

These models describe only artifacts and protocol boundaries that the host has
already selected. They intentionally do not accept tenant-controlled paths,
model identifiers, credentials, tools, or profile implementations.
"""

from __future__ import annotations

import json
import math
import re
from enum import StrEnum
from pathlib import Path, PurePosixPath
from typing import Any, Final, Literal

from pydantic import Field, TypeAdapter, field_validator, model_validator

from ecms.shared.models.base import ImmutableModel

__all__ = [
    "AgentStepEnvelope",
    "CapabilityRequest",
    "DSHProfileSpec",
    "EnvelopeValidationError",
    "ProfileExecutionBudget",
    "RuntimeReadiness",
    "StageSpec",
    "StepOutcomeKind",
    "TerminalResult",
    "parse_step_envelope",
]

_IDENTIFIER_RE: Final[re.Pattern[str]] = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
_ENVIRONMENT_NAME_RE: Final[re.Pattern[str]] = re.compile(r"^[A-Z][A-Z0-9_]{0,127}$")
_VERSION_RE: Final[re.Pattern[str]] = re.compile(r"^[0-9A-Za-z][0-9A-Za-z.+-]{0,127}$")
MAX_ENVELOPE_BYTES: Final[int] = 64 * 1024

type JSONValue = dict[str, JSONValue] | list[JSONValue] | str | int | float | bool | None


class EnvelopeValidationError(ValueError):
    """Raised when DSH output is not a permitted host action envelope."""


class StepOutcomeKind(StrEnum):
    """The only outcomes the host may accept from one DSH step."""

    TERMINAL = "terminal"
    CAPABILITY_REQUEST = "capability_request"


class ProfileExecutionBudget(ImmutableModel):
    """Bounded non-secret subprocess policy selected by the host."""

    timeout_seconds: float = Field(default=300, gt=0, le=1_800)
    shutdown_grace_seconds: float = Field(default=5, gt=0, le=60)
    profile_lock_timeout_seconds: float = Field(default=30, gt=0, le=300)
    max_task_bytes: int = Field(default=96 * 1024, ge=1_024, le=512 * 1024)
    max_command_bytes: int = Field(default=112 * 1024, ge=1_024, le=768 * 1024)
    max_stdout_bytes: int = Field(default=1 * 1024 * 1024, ge=1_024, le=8 * 1024 * 1024)
    max_stderr_bytes: int = Field(default=256 * 1024, ge=1_024, le=2 * 1024 * 1024)

    @model_validator(mode="after")
    def validate_cross_budget_bounds(self) -> ProfileExecutionBudget:
        """Reject impossible task/argv limits before a profile can run."""
        if self.max_command_bytes < self.max_task_bytes:
            raise ValueError("max_command_bytes must be at least max_task_bytes")
        return self


class StageSpec(ImmutableModel):
    """Profile-owned stage vocabulary and safe execution limits."""

    stage_id: str
    request_schema_ref: str
    terminal_schema_ref: str
    max_repair_attempts: Literal[0, 1] = 1
    max_capability_requests: int = Field(default=0, ge=0, le=32)
    capability_ids: tuple[str, ...] = ()

    @field_validator("stage_id")
    @classmethod
    def validate_stage_id(cls, value: str) -> str:
        """Keep profile stage identifiers deterministic and host-addressable."""
        return _validate_identifier(value, label="stage_id")

    @field_validator("request_schema_ref", "terminal_schema_ref")
    @classmethod
    def validate_schema_ref(cls, value: str) -> str:
        """Require a stable local schema reference, never a remote URL."""
        if not isinstance(value, str) or not value.strip():
            raise ValueError("schema reference must be a non-empty string")
        if "://" in value or "\x00" in value:
            raise ValueError("schema reference must be local and contain no NUL bytes")
        return value.strip()

    @field_validator("capability_ids")
    @classmethod
    def validate_capability_ids(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Prevent duplicate or malformed capability references in one stage."""
        normalized = tuple(_validate_identifier(item, label="capability_id") for item in value)
        if len(set(normalized)) != len(normalized):
            raise ValueError("capability_ids must not contain duplicates")
        return normalized

    @model_validator(mode="after")
    def validate_capability_budget(self) -> StageSpec:
        """Do not let a stage request undeclared capabilities."""
        if self.max_capability_requests > 0 and not self.capability_ids:
            raise ValueError("capability_ids are required when capability requests are allowed")
        if self.max_capability_requests == 0 and self.capability_ids:
            raise ValueError("capability_ids require a positive max_capability_requests")
        return self


class DSHProfileSpec(ImmutableModel):
    """An installed, deployment-owned DSH profile artifact contract."""

    profile_id: str
    version: str
    asset_root: Path
    stages: tuple[StageSpec, ...]
    required_assets: tuple[str, ...] = (
        "package.json",
        "pnpm-workspace.yaml",
        "cordis.patch.yml",
    )
    required_environment: tuple[str, ...] = ()
    generated_environment: tuple[str, ...] = ()
    required_bundles: tuple[str, ...] = (
        "@deepseek-ai/dsh-base",
        "@deepseek-ai/dsh-headless",
    )
    execution_budget: ProfileExecutionBudget = Field(default_factory=ProfileExecutionBudget)

    @field_validator("profile_id")
    @classmethod
    def validate_profile_id(cls, value: str) -> str:
        """Accept only a stable profile identifier, never an arbitrary path."""
        return _validate_identifier(value, label="profile_id")

    @field_validator("version")
    @classmethod
    def validate_version(cls, value: str) -> str:
        """Require a bounded deployment version string."""
        if not isinstance(value, str) or not _VERSION_RE.fullmatch(value.strip()):
            raise ValueError("version must be a stable non-empty version string")
        return value.strip()

    @field_validator("asset_root")
    @classmethod
    def validate_asset_root(cls, value: Path) -> Path:
        """Keep artifact locations host-selected and normalized."""
        if not isinstance(value, Path):
            raise ValueError("asset_root must be a path")
        if not value.is_absolute():
            raise ValueError("asset_root must be an absolute deployment-owned path")
        return value

    @field_validator("stages")
    @classmethod
    def validate_stages(cls, value: tuple[StageSpec, ...]) -> tuple[StageSpec, ...]:
        """Require at least one unambiguous stage in every profile."""
        if not value:
            raise ValueError("at least one stage is required")
        identifiers = tuple(stage.stage_id for stage in value)
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("stage identifiers must be unique within a profile")
        return value

    @field_validator("required_assets")
    @classmethod
    def validate_required_assets(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Reject traversing or duplicate profile asset names."""
        if not value:
            raise ValueError("required_assets must not be empty")
        normalized = tuple(_validate_relative_asset(item) for item in value)
        if len(set(normalized)) != len(normalized):
            raise ValueError("required_assets must not contain duplicates")
        return normalized

    @field_validator("required_environment", "generated_environment")
    @classmethod
    def validate_environment_names(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Constrain profile-requested child environment variable names."""
        normalized = tuple(_validate_environment_name(item) for item in value)
        if len(set(normalized)) != len(normalized):
            raise ValueError("environment names must not contain duplicates")
        return normalized

    @field_validator("required_bundles")
    @classmethod
    def validate_required_bundles(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Require a non-empty, duplicate-free declared DSH bundle set."""
        if not value:
            raise ValueError("required_bundles must not be empty")
        normalized = tuple(item.strip() for item in value)
        if any(not item or "\x00" in item for item in normalized):
            raise ValueError("required bundle names must be non-empty and NUL-free")
        if len(set(normalized)) != len(normalized):
            raise ValueError("required_bundles must not contain duplicates")
        return normalized

    @model_validator(mode="after")
    def validate_environment_sets(self) -> DSHProfileSpec:
        """A host-generated value cannot also be required from deployment config."""
        overlap = set(self.required_environment).intersection(self.generated_environment)
        if overlap:
            raise ValueError(
                "required_environment and generated_environment overlap: "
                + ", ".join(sorted(overlap))
            )
        return self

    @property
    def identity(self) -> str:
        """Return the immutable registered artifact identity."""
        return f"{self.profile_id}@{self.version}"

    def stage(self, stage_id: str) -> StageSpec:
        """Resolve a declared stage or fail before DSH invocation."""
        normalized = _validate_identifier(stage_id, label="stage_id")
        for stage in self.stages:
            if stage.stage_id == normalized:
                return stage
        raise KeyError(f"profile {self.identity} does not declare stage {normalized!r}")

    def fingerprint_payload(self) -> bytes:
        """Return deterministic non-secret spec bytes for runtime fingerprinting."""
        payload = {
            "profile_id": self.profile_id,
            "version": self.version,
            "required_assets": self.required_assets,
            "required_bundles": self.required_bundles,
            "required_environment": self.required_environment,
            "generated_environment": self.generated_environment,
            "stages": [
                {
                    "stage_id": stage.stage_id,
                    "request_schema_ref": stage.request_schema_ref,
                    "terminal_schema_ref": stage.terminal_schema_ref,
                    "max_repair_attempts": stage.max_repair_attempts,
                    "max_capability_requests": stage.max_capability_requests,
                    "capability_ids": stage.capability_ids,
                }
                for stage in self.stages
            ],
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


class RuntimeReadiness(ImmutableModel):
    """Non-secret, side-effect-free profile runtime preflight result."""

    ready: bool
    profile_identity: str
    reason_code: str | None = None
    profile_fingerprint: str | None = None

    @field_validator("profile_identity")
    @classmethod
    def validate_profile_identity(cls, value: str) -> str:
        """Keep readiness reports stable and safe for operational labels."""
        if not isinstance(value, str) or "@" not in value or not value.strip():
            raise ValueError("profile_identity must be a non-empty profile identity")
        return value.strip()

    @model_validator(mode="after")
    def validate_state(self) -> RuntimeReadiness:
        """Require an operational reason exactly when the profile is unready."""
        if self.ready and self.reason_code is not None:
            raise ValueError("ready status cannot contain a reason_code")
        if not self.ready and not self.reason_code:
            raise ValueError("unready status requires a reason_code")
        return self


class TerminalResult(ImmutableModel):
    """Validated terminal DSH output awaiting profile-specific result validation."""

    envelope_version: Literal["aegis.agent-step.v1"]
    outcome: Literal[StepOutcomeKind.TERMINAL]
    stage_id: str
    result: Any

    @field_validator("stage_id")
    @classmethod
    def validate_stage_id(cls, value: str) -> str:
        """Ensure the host can match output to the selected profile stage."""
        return _validate_identifier(value, label="stage_id")

    @field_validator("result")
    @classmethod
    def validate_result(cls, value: Any) -> Any:
        """Permit only JSON values before a profile validates its result schema."""
        _ensure_json_value(value, path="result")
        return value


class CapabilityRequest(ImmutableModel):
    """Validated request for a named host-mediated capability invocation."""

    envelope_version: Literal["aegis.agent-step.v1"]
    outcome: Literal[StepOutcomeKind.CAPABILITY_REQUEST]
    stage_id: str
    capability_id: str
    capability_version: str
    idempotency_key: str = Field(min_length=1, max_length=128)
    arguments: dict[str, Any]

    @field_validator("stage_id", "capability_id")
    @classmethod
    def validate_identifier_fields(cls, value: str) -> str:
        """Keep stage and capability routing names host-addressable."""
        return _validate_identifier(value, label="identifier")

    @field_validator("capability_version")
    @classmethod
    def validate_capability_version(cls, value: str) -> str:
        """Require a bounded capability contract version."""
        if not isinstance(value, str) or not _VERSION_RE.fullmatch(value.strip()):
            raise ValueError("capability_version must be a stable non-empty version string")
        return value.strip()

    @field_validator("idempotency_key")
    @classmethod
    def validate_idempotency_key(cls, value: str) -> str:
        """Keep host idempotency values bounded and free from control bytes."""
        if "\x00" in value or any(ord(character) < 32 for character in value):
            raise ValueError("idempotency_key must not contain control characters")
        return value

    @field_validator("arguments")
    @classmethod
    def validate_arguments(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject non-JSON capability payloads before policy evaluation."""
        _ensure_json_value(value, path="arguments")
        return value


type AgentStepEnvelope = TerminalResult | CapabilityRequest


def parse_step_envelope(
    output: str | bytes,
    *,
    max_bytes: int = MAX_ENVELOPE_BYTES,
) -> AgentStepEnvelope:
    """Parse one strict DSH result envelope without granting any capability.

    This function only verifies wire shape. The caller must still validate the
    selected stage, profile capability declaration, tenant scope, grant,
    approval, idempotency, budget, and worker lease before taking any effect.
    """
    if not isinstance(max_bytes, int) or max_bytes < 1:
        raise ValueError("max_bytes must be a positive integer")
    if isinstance(output, str):
        encoded = output.encode("utf-8")
    elif isinstance(output, bytes):
        encoded = output
    else:
        raise EnvelopeValidationError("DSH output must be text or UTF-8 bytes")
    if len(encoded) > max_bytes:
        raise EnvelopeValidationError("DSH output envelope exceeds the configured byte limit")
    try:
        decoded = encoded.decode("utf-8")
        payload = json.loads(decoded)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise EnvelopeValidationError("DSH output must be one JSON object envelope") from error
    if not isinstance(payload, dict):
        raise EnvelopeValidationError("DSH output envelope must be a JSON object")

    outcome = payload.get("outcome")
    try:
        if outcome == StepOutcomeKind.TERMINAL:
            return TypeAdapter(TerminalResult).validate_python(payload)
        if outcome == StepOutcomeKind.CAPABILITY_REQUEST:
            return TypeAdapter(CapabilityRequest).validate_python(payload)
    except ValueError as error:
        raise EnvelopeValidationError("DSH output envelope failed validation") from error
    raise EnvelopeValidationError("DSH output envelope has an unknown outcome")


def _validate_identifier(value: str, *, label: str) -> str:
    """Validate a bounded identifier accepted in host routing keys."""
    if not isinstance(value, str) or not _IDENTIFIER_RE.fullmatch(value.strip()):
        raise ValueError(f"{label} must be a lowercase dotted, dashed, or underscored identifier")
    return value.strip()


def _validate_environment_name(value: str) -> str:
    """Validate an environment name without allowing arbitrary child env input."""
    if not isinstance(value, str) or not _ENVIRONMENT_NAME_RE.fullmatch(value.strip()):
        raise ValueError("environment names must be uppercase shell variable names")
    return value.strip()


def _validate_relative_asset(value: str) -> str:
    """Validate a profile asset path without allowing filesystem traversal."""
    if not isinstance(value, str) or not value.strip() or "\x00" in value:
        raise ValueError("required asset names must be non-empty and NUL-free")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError("required asset names must be safe relative paths")
    return path.as_posix()


def _ensure_json_value(value: Any, *, path: str) -> None:
    """Reject values that cannot cross a JSON-only DSH/host protocol boundary."""
    if value is None or isinstance(value, (str, bool, int)):
        return
    if isinstance(value, float):
        if math.isfinite(value):
            return
        raise ValueError(f"{path} contains a non-finite float")
    if isinstance(value, list):
        for index, item in enumerate(value):
            _ensure_json_value(item, path=f"{path}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError(f"{path} contains a non-string object key")
            _ensure_json_value(item, path=f"{path}.{key}")
        return
    raise ValueError(f"{path} contains a non-JSON value")

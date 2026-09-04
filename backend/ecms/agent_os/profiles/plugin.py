"""Profile plugin interfaces layered on the existing application plugin lifecycle."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping
from typing import Any

from ecms.agent_os.profiles.contracts import (
    AgentStepEnvelope,
    DSHProfileSpec,
    RuntimeReadiness,
    StageSpec,
    TerminalResult,
)
from ecms.plugins.infrastructure.base import BasePlugin

__all__ = [
    "AgentProfileCatalog",
    "AgentProfilePlugin",
    "ProfileContractError",
    "ProfileNotRegisteredError",
]


class ProfileContractError(ValueError):
    """Raised when an installed profile violates its declared contract."""


class ProfileNotRegisteredError(LookupError):
    """Raised when a host-selected profile identity is not installed."""


class AgentProfilePlugin(BasePlugin, ABC):
    """Lifecycle-managed implementation of one installed Agent OS profile.

    ``PluginRegistry`` remains responsible for registration, dependency order,
    and lifecycle management. This base class owns only profile-specific
    validation and prompt/result behavior once that registry has selected a
    deployment-installed plugin.
    """

    @property
    @abstractmethod
    def profile_spec(self) -> DSHProfileSpec:
        """Return the immutable artifact contract for this installed profile."""

    def stage_spec(self, stage_id: str) -> StageSpec:
        """Resolve an explicit declared stage; unknown stages never fall through."""
        try:
            return self.profile_spec.stage(stage_id)
        except KeyError as error:
            raise ProfileContractError(str(error)) from error

    def validate(self) -> None:
        """Validate static profile policy in addition to the base lifecycle hook."""
        super().validate()
        spec = self.profile_spec
        manifest = self.manifest
        if not manifest.name.strip():
            raise ProfileContractError("profile plugin manifest name must not be empty")
        for stage in spec.stages:
            unknown = set(stage.capability_ids).difference(self.capability_ids)
            if unknown:
                raise ProfileContractError(
                    f"stage {stage.stage_id!r} references undeclared capabilities: "
                    + ", ".join(sorted(unknown))
                )

    @property
    def capability_ids(self) -> frozenset[str]:
        """Return all capability IDs this profile may request across its stages."""
        return frozenset(
            capability_id
            for stage in self.profile_spec.stages
            for capability_id in stage.capability_ids
        )

    @abstractmethod
    def validate_request(self, stage: StageSpec, request: Mapping[str, Any]) -> None:
        """Validate profile-owned stage input before rendering a DSH prompt."""

    @abstractmethod
    def render_prompt(self, stage: StageSpec, request: Mapping[str, Any]) -> str:
        """Return bounded host-rendered prompt text for the selected stage."""

    @abstractmethod
    def validate_terminal_result(self, stage: StageSpec, result: TerminalResult) -> Any:
        """Validate a terminal envelope result against the profile-owned schema."""

    def validate_envelope(self, stage: StageSpec, envelope: AgentStepEnvelope) -> None:
        """Enforce generic stage/capability bounds before capability policy runs."""
        if envelope.stage_id != stage.stage_id:
            raise ProfileContractError(
                f"DSH output stage {envelope.stage_id!r} does not match {stage.stage_id!r}"
            )
        if isinstance(envelope, TerminalResult):
            return
        if envelope.capability_id not in stage.capability_ids:
            raise ProfileContractError(
                f"stage {stage.stage_id!r} is not allowed to request "
                f"capability {envelope.capability_id!r}"
            )
        if stage.max_capability_requests == 0:
            raise ProfileContractError(
                f"stage {stage.stage_id!r} does not permit capability requests"
            )

    def readiness(self) -> RuntimeReadiness:
        """Report static plugin readiness; runtime preflight is layered separately."""
        return RuntimeReadiness(ready=True, profile_identity=self.profile_spec.identity)


class AgentProfileCatalog:
    """Resolve already lifecycle-registered profiles without duplicating lifecycle.

    Application composition builds this catalog from the instances registered
    through ``PluginRegistry``. It deliberately has no initialize/start/stop
    methods and never discovers code or reads tenant activation data.
    """

    def __init__(self, profiles: Iterable[AgentProfilePlugin] = ()) -> None:
        """Build a catalog from already lifecycle-registered profile instances."""
        self._profiles: dict[tuple[str, str], AgentProfilePlugin] = {}
        for profile in profiles:
            self.register(profile)

    def register(self, profile: AgentProfilePlugin) -> None:
        """Add one validated deployment-installed profile implementation."""
        if not isinstance(profile, AgentProfilePlugin):
            raise TypeError("profile must implement AgentProfilePlugin")
        profile.validate()
        key = (profile.profile_spec.profile_id, profile.profile_spec.version)
        if key in self._profiles:
            raise ProfileContractError(
                f"duplicate installed Agent OS profile {profile.profile_spec.identity}"
            )
        self._profiles[key] = profile

    def resolve(self, profile_id: str, version: str | None = None) -> AgentProfilePlugin:
        """Resolve one installed profile; ambiguity fails closed."""
        candidates = [
            profile
            for (installed_id, installed_version), profile in self._profiles.items()
            if installed_id == profile_id and (version is None or installed_version == version)
        ]
        if not candidates:
            suffix = f"@{version}" if version is not None else ""
            raise ProfileNotRegisteredError(
                f"Agent OS profile {profile_id}{suffix} is not installed"
            )
        if len(candidates) != 1:
            raise ProfileContractError(
                f"Agent OS profile {profile_id!r} has multiple installed versions; "
                "an explicit version is required"
            )
        return candidates[0]

    def installed(self) -> tuple[AgentProfilePlugin, ...]:
        """Return installed profiles in deterministic profile identity order."""
        return tuple(
            self._profiles[key]
            for key in sorted(self._profiles, key=lambda item: (item[0], item[1]))
        )

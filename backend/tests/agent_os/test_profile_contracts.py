"""Contract tests for profile-neutral Agent OS boundaries."""

from __future__ import annotations

import tempfile
import unittest
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ecms.agent_os.capabilities.contracts import (
    CapabilityEffect,
    CapabilitySpec,
)
from ecms.agent_os.profiles.contracts import (
    CapabilityRequest,
    DSHProfileSpec,
    EnvelopeValidationError,
    StageSpec,
    TerminalResult,
    parse_step_envelope,
)
from ecms.agent_os.profiles.plugin import (
    AgentProfileCatalog,
    AgentProfilePlugin,
    ProfileContractError,
    ProfileNotRegisteredError,
)
from ecms.plugins.domain.manifest import PluginManifest


class _Profile(AgentProfilePlugin):
    def __init__(self, spec: DSHProfileSpec) -> None:
        self._spec = spec

    @property
    def manifest(self) -> PluginManifest:
        return PluginManifest(
            name=f"agent-profile.{self._spec.profile_id}", version=self._spec.version
        )

    @property
    def profile_spec(self) -> DSHProfileSpec:
        return self._spec

    def validate_request(self, stage: StageSpec, request: Mapping[str, Any]) -> None:
        if not request:
            raise ValueError("request is required")

    def render_prompt(self, stage: StageSpec, request: Mapping[str, Any]) -> str:
        return f"{stage.stage_id}:{request['source']}"

    def validate_terminal_result(self, stage: StageSpec, result: TerminalResult) -> Any:
        return result.result


class AgentOSProfileContractTests(unittest.TestCase):
    def _spec(
        self, *, profile_id: str = "project-context", version: str = "1.0.0"
    ) -> DSHProfileSpec:
        root = Path(tempfile.gettempdir()) / "agent-os-profile"
        return DSHProfileSpec(
            profile_id=profile_id,
            version=version,
            asset_root=root,
            stages=(
                StageSpec(
                    stage_id="summarize",
                    request_schema_ref="schemas/request.json",
                    terminal_schema_ref="schemas/result.json",
                    max_capability_requests=1,
                    capability_ids=("knowledge.search",),
                ),
            ),
        )

    def test_profile_spec_has_stable_identity_and_fingerprint_input(self) -> None:
        spec = self._spec()

        self.assertEqual(spec.identity, "project-context@1.0.0")
        self.assertEqual(spec.stage("summarize").terminal_schema_ref, "schemas/result.json")
        self.assertIn(b'"profile_id":"project-context"', spec.fingerprint_payload())
        with self.assertRaises(KeyError):
            spec.stage("unknown")

    def test_envelope_parser_accepts_only_explicit_outcomes(self) -> None:
        terminal = parse_step_envelope(
            '{"envelope_version":"aegis.agent-step.v1","outcome":"terminal",'
            '"stage_id":"summarize","result":{"summary":"safe"}}'
        )
        capability = parse_step_envelope(
            '{"envelope_version":"aegis.agent-step.v1","outcome":"capability_request",'
            '"stage_id":"summarize","capability_id":"knowledge.search",'
            '"capability_version":"1.0.0","idempotency_key":"request-1",'
            '"arguments":{"query":"project context"}}'
        )

        self.assertIsInstance(terminal, TerminalResult)
        self.assertIsInstance(capability, CapabilityRequest)
        with self.assertRaises(EnvelopeValidationError):
            parse_step_envelope('{"outcome":"shell"}')
        with self.assertRaises(EnvelopeValidationError):
            parse_step_envelope(
                '{"envelope_version":"aegis.agent-step.v1","outcome":"terminal",'
                '"stage_id":"summarize","result":{},"tool":"shell"}'
            )

    def test_catalog_fails_closed_for_missing_ambiguous_and_duplicate_profiles(self) -> None:
        first = _Profile(self._spec(version="1.0.0"))
        second = _Profile(self._spec(version="2.0.0"))
        catalog = AgentProfileCatalog((first, second))

        with self.assertRaises(ProfileContractError):
            catalog.resolve("project-context")
        self.assertIs(catalog.resolve("project-context", "1.0.0"), first)
        with self.assertRaises(ProfileNotRegisteredError):
            catalog.resolve("missing", "1.0.0")
        with self.assertRaises(ProfileContractError):
            catalog.register(_Profile(self._spec(version="1.0.0")))

    def test_non_read_capabilities_require_approval_and_idempotency(self) -> None:
        with self.assertRaisesRegex(ValueError, "require approval"):
            CapabilitySpec(
                capability_id="project.write",
                version="1.0.0",
                effect=CapabilityEffect.WRITE,
                request_schema_ref="schemas/request.json",
                result_schema_ref="schemas/result.json",
            )
        spec = CapabilitySpec(
            capability_id="knowledge.search",
            version="1.0.0",
            effect=CapabilityEffect.READ,
            request_schema_ref="schemas/request.json",
            result_schema_ref="schemas/result.json",
        )
        self.assertEqual(spec.effect, CapabilityEffect.READ)


if __name__ == "__main__":
    unittest.main()

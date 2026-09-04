"""Contract tests for the inactive read-only Compliance Officer profile."""

from __future__ import annotations

import unittest

from ecms.agent.ba.dsh_profile import business_analyst_dsh_profile_spec
from ecms.agent.compliance_officer.plugin import ComplianceOfficerProfilePlugin
from ecms.agent_os.profiles.contracts import CapabilityRequest, TerminalResult
from ecms.agent_os.profiles.plugin import AgentProfileCatalog, ProfileContractError


class ComplianceOfficerProfileTests(unittest.TestCase):
    """Prove the second profile uses shared Agent OS contracts without BA stages."""

    def setUp(self) -> None:
        self.plugin = ComplianceOfficerProfilePlugin()
        self.stage = self.plugin.stage_spec("assess")

    def test_declares_one_read_only_assessment_stage(self) -> None:
        spec = self.plugin.profile_spec
        ba_stage_ids = {
            stage.stage_id for stage in business_analyst_dsh_profile_spec().stages
        }
        compliance_stage_ids = {stage.stage_id for stage in spec.stages}

        self.assertEqual(spec.identity, "compliance-officer@1.0.0")
        self.assertEqual(tuple(stage.stage_id for stage in spec.stages), ("assess",))
        self.assertEqual(self.stage.max_capability_requests, 2)
        self.assertEqual(self.stage.capability_ids, ("knowledge.search.v1",))
        self.assertEqual(self.plugin.capability_ids, frozenset({"knowledge.search.v1"}))
        self.assertFalse(ba_stage_ids.intersection(compliance_stage_ids))
        self.plugin.validate()

    def test_catalog_registration_does_not_activate_the_profile(self) -> None:
        catalog = AgentProfileCatalog((self.plugin,))

        self.assertIs(catalog.resolve("compliance-officer", "1.0.0"), self.plugin)
        self.assertEqual(
            tuple(profile.profile_spec.identity for profile in catalog.installed()),
            ("compliance-officer@1.0.0",),
        )

    def test_request_prompt_and_terminal_result_are_profile_owned_and_bounded(self) -> None:
        request = {"brief": "Assess the supplied SOC 2 evidence."}

        self.plugin.validate_request(self.stage, request)
        prompt = self.plugin.render_prompt(self.stage, request)
        result = self.plugin.validate_terminal_result(
            self.stage,
            TerminalResult(
                envelope_version="aegis.agent-step.v1",
                outcome="terminal",
                stage_id="assess",
                result={"verified": [], "gaps": ["retention evidence missing"]},
            ),
        )

        self.assertIn("untrusted reference data", prompt)
        self.assertEqual(result["gaps"], ["retention evidence missing"])
        with self.assertRaisesRegex(ProfileContractError, "non-empty brief"):
            self.plugin.validate_request(self.stage, {"brief": ""})

    def test_rejects_any_capability_except_the_declared_read_capability(self) -> None:
        allowed = CapabilityRequest(
            envelope_version="aegis.agent-step.v1",
            outcome="capability_request",
            stage_id="assess",
            capability_id="knowledge.search.v1",
            capability_version="1.0.0",
            idempotency_key="compliance-evidence-1",
            arguments={"query": "retention control evidence"},
        )
        disallowed = allowed.model_copy(
            update={"capability_id": "project.write.v1"}
        )

        self.plugin.validate_envelope(self.stage, allowed)
        with self.assertRaisesRegex(ProfileContractError, "not allowed"):
            self.plugin.validate_envelope(self.stage, disallowed)


if __name__ == "__main__":
    unittest.main()

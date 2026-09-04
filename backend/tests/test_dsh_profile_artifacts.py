"""Integration-free preflight tests for deployment-owned DSH profile artifacts."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ecms.agent import dsh_runtime
from ecms.agent.ba.dsh_profile import business_analyst_dsh_profile_spec
from ecms.agent.compliance_officer.dsh_profile import compliance_officer_dsh_profile_spec
from ecms.agent.dsh_runtime import DSHRuntime


class DSHProfileArtifactPreflightTests(unittest.TestCase):
    """Validate real artifacts without registering, activating, or invoking a profile."""

    @staticmethod
    def _stub_executable(root: Path) -> Path:
        executable = root / "dsh-stub"
        executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        executable.chmod(0o755)
        return executable

    def test_real_deployment_profiles_preflight_with_tagged_cordis_patches(self) -> None:
        specs = (
            business_analyst_dsh_profile_spec(),
            compliance_officer_dsh_profile_spec(),
        )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable = self._stub_executable(root)
            for spec in specs:
                with self.subTest(profile=spec.identity):
                    patch = (spec.asset_root / "cordis.patch.yml").read_text(encoding="utf-8")
                    runtime = DSHRuntime(
                        profile_spec=spec,
                        dsh_home=root / spec.profile_id / "dsh-home",
                        dsh_executable=executable,
                        env={
                            "ANTHROPIC_BASE_URL": "https://gateway.test",
                            "ANTHROPIC_AUTH_TOKEN": "test-token",
                        },
                    )

                    readiness = runtime.preflight()
                    repeated_readiness = runtime.preflight()

                    self.assertIn("!!js", patch)
                    self.assertTrue(readiness.ready)
                    self.assertEqual(readiness.profile_identity, spec.identity)
                    self.assertIsNotNone(readiness.profile_fingerprint)
                    self.assertEqual(
                        readiness.profile_fingerprint,
                        repeated_readiness.profile_fingerprint,
                    )
                    self.assertFalse((root / spec.profile_id / "dsh-home").exists())

    def test_compliance_preflight_fails_closed_without_gateway_configuration(self) -> None:
        spec = compliance_officer_dsh_profile_spec()

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runtime = DSHRuntime(
                profile_spec=spec,
                dsh_home=root / "dsh-home",
                dsh_executable=self._stub_executable(root),
            )
            with patch.dict(dsh_runtime.os.environ, {}, clear=True):
                readiness = runtime.preflight()

            self.assertFalse(readiness.ready)
            self.assertEqual(readiness.reason_code, "profile_environment_invalid")
            self.assertFalse((root / "dsh-home").exists())

    def test_compliance_artifact_has_no_legacy_descriptor(self) -> None:
        spec = compliance_officer_dsh_profile_spec()

        self.assertFalse((spec.asset_root / "dsh.profile").exists())
        self.assertEqual(spec.profile_id, "compliance-officer")
        self.assertEqual(tuple(stage.stage_id for stage in spec.stages), ("assess",))


if __name__ == "__main__":
    unittest.main()

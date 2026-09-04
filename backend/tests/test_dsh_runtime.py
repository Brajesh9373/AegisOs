"""Regression coverage for the repository-owned DeepSeek Harness boundary.

These tests use a local executable stub; they never call a model gateway or
replace the real DSH runtime in production.
"""

from __future__ import annotations

import asyncio
import json
import os
import shlex
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ecms.agent import dsh_runtime
from ecms.agent_os.profiles.contracts import DSHProfileSpec, StageSpec
from ecms.agent.dsh_runtime import (
    DSHExecutionError,
    DSHExecutionResult,
    DSHProfileNotFoundError,
    DSHRuntime,
    _json_object,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PROFILE_DIR = (
    REPO_ROOT / "packages" / "dsh-integration" / "profiles" / "business-analyst"
)


class DSHProfileContractTests(unittest.TestCase):
    def test_business_analyst_profile_declares_real_dsh_bundles_and_glm_route(self) -> None:
        manifest = json.loads((PROFILE_DIR / "package.json").read_text(encoding="utf-8"))
        bundles = manifest["dsh"]["profile"]["bundles"]
        self.assertEqual(bundles, ["@deepseek-ai/dsh-base", "@deepseek-ai/dsh-headless"])

        # The pinned DSH CLI validates YAML composition during the integration
        # smoke test. Keep this unit-level contract dependency-free so it can run
        # in the backend test environment without a second YAML parser.
        patch_text = (PROFILE_DIR / "cordis.patch.yml").read_text(encoding="utf-8")
        first_content_line = next(
            line for line in patch_text.splitlines() if line.strip() and not line.startswith("#")
        )
        self.assertEqual(first_content_line, "- id: llm-pi-ai")
        self.assertEqual(
            [line.strip() for line in patch_text.splitlines() if line.startswith("- id:")],
            ["- id: llm-pi-ai", "- id: agent-default-model", "- id: system-prompt"],
        )
        self.assertIn("glm-gateway:", patch_text)
        self.assertIn("api: anthropic-messages", patch_text)
        self.assertIn("- id: glm-5", patch_text)
        self.assertIn("provider: glm-gateway", patch_text)
        self.assertIn("model: glm-5", patch_text)
        self.assertIn("process.env.ANTHROPIC_BASE_URL", patch_text)
        self.assertIn("process.env.ANTHROPIC_AUTH_TOKEN", patch_text)
        self.assertIn("process.env.CLAUDE_CODE_SESSION_ID", patch_text)
        self.assertIn("untrusted reference data", patch_text)
        self.assertIn(
            '"background|pain_points|assumptions|architectural_depth|execution_stages|timelines"',
            patch_text,
        )
        self.assertNotIn("{{cwd}}", patch_text)
        self.assertNotIn("apiKeyEnv", patch_text)
        self.assertFalse((PROFILE_DIR / "dsh.profile").exists())


class DSHRuntimeTests(unittest.IsolatedAsyncioTestCase):
    @staticmethod
    def _create_profile_source(root: Path) -> Path:
        source = root / "source-profile"
        source.mkdir()
        (source / "package.json").write_text(
            json.dumps(
                {
                    "name": "test-profile",
                    "dsh": {
                        "profile": {
                            "bundles": ["@deepseek-ai/dsh-base", "@deepseek-ai/dsh-headless"]
                        }
                    },
                }
            ),
            encoding="utf-8",
        )
        (source / "pnpm-workspace.yaml").write_text("packages:\n  - .\n", encoding="utf-8")
        (source / "cordis.patch.yml").write_text("[]\n", encoding="utf-8")
        return source

    @staticmethod
    def _profile_spec(
        source: Path,
        *,
        profile_id: str = "business-analyst",
        required_environment: tuple[str, ...] = ("ANTHROPIC_BASE_URL", "ANTHROPIC_AUTH_TOKEN"),
    ) -> DSHProfileSpec:
        return DSHProfileSpec(
            profile_id=profile_id,
            version="test",
            asset_root=source,
            required_environment=required_environment,
            generated_environment=("CLAUDE_CODE_SESSION_ID",),
            stages=(
                StageSpec(
                    stage_id="test",
                    request_schema_ref="schemas/request.json",
                    terminal_schema_ref="schemas/result.json",
                    max_repair_attempts=0,
                ),
            ),
        )

    @staticmethod
    def _create_executable(root: Path, body: str | None = None) -> Path:
        executable = root / "dsh-stub"
        executable.write_text(
            body
            or "#!/bin/sh\nprintf 'DSH stub completed\\n'\nprintf '%s' \"$CLAUDE_CODE_SESSION_ID\" >&2\n",
            encoding="utf-8",
        )
        executable.chmod(0o755)
        return executable

    def _runtime(self, root: Path, executable: Path, **kwargs: object) -> DSHRuntime:
        source = self._create_profile_source(root)
        return DSHRuntime(
            profile_spec=self._profile_spec(source),
            dsh_home=root / "dsh-home",
            env={
                "ANTHROPIC_BASE_URL": "https://gateway.test",
                "ANTHROPIC_AUTH_TOKEN": "sensitive-token",
                "CLAUDE_CODE_SESSION_ID": "test-session",
            },
            dsh_executable=executable,
            **kwargs,
        )

    def test_synchronize_publishes_immutable_profile_versions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runtime = self._runtime(root, self._create_executable(root))
            source = runtime._profile_source

            first = runtime._synchronize_profile()
            first_profile = runtime._profile_dir_for(first)
            generated = first_profile / "cordis.yml"
            generated.write_text("generated by DSH", encoding="utf-8")
            (source / "cordis.patch.yml").write_text("- id: changed\n", encoding="utf-8")

            second = runtime._synchronize_profile()
            second_profile = runtime._profile_dir_for(second)

            self.assertNotEqual(first, second)
            self.assertEqual(
                (first_profile / "cordis.patch.yml").read_text(encoding="utf-8"), "[]\n"
            )
            self.assertEqual(generated.read_text(encoding="utf-8"), "generated by DSH")
            self.assertEqual(
                (second_profile / "cordis.patch.yml").read_text(encoding="utf-8"), "- id: changed\n"
            )

    def test_child_environment_is_allowlisted_and_gateway_values_normalized(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runtime = self._runtime(root, self._create_executable(root))
            with patch.dict(
                dsh_runtime.os.environ,
                {
                    "DATABASE_URL": "postgresql://must-not-reach-child",
                    "UNRELATED_SECRET": "must-not-reach-child",
                    "PATH": "/usr/bin",
                },
                clear=True,
            ):
                environment = runtime._build_env(execution_home=root / "isolated-home")

            self.assertEqual(environment["ANTHROPIC_BASE_URL"], "https://gateway.test")
            self.assertEqual(environment["ANTHROPIC_AUTH_TOKEN"], "sensitive-token")
            self.assertEqual(environment["DSH_HOME"], str(root / "isolated-home"))
            self.assertNotIn("DATABASE_URL", environment)
            self.assertNotIn("UNRELATED_SECRET", environment)

    def test_gateway_preflight_rejects_missing_token(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = self._create_profile_source(root)
            runtime = DSHRuntime(
                profile_spec=self._profile_spec(source),
                dsh_home=root / "dsh-home",
                env={"ANTHROPIC_BASE_URL": "https://gateway.test"},
                dsh_executable=self._create_executable(root),
            )
            with patch.dict(dsh_runtime.os.environ, {"ANTHROPIC_AUTH_TOKEN": ""}):
                with self.assertRaisesRegex(DSHExecutionError, "ANTHROPIC_AUTH_TOKEN"):
                    runtime._build_env()

    def test_requires_pinned_repository_executable_when_no_explicit_override(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runtime = self._runtime(root, self._create_executable(root))
            runtime._integration_root = root / "missing-integration"
            with patch.object(dsh_runtime.shutil, "which", return_value="/usr/local/bin/dsh"):
                with self.assertRaisesRegex(DSHExecutionError, "pinned integration dependency"):
                    runtime._resolve_dsh_executable(None)

    def test_missing_or_malformed_profile_assets_are_reported_before_execution(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = self._create_profile_source(root)
            runtime = DSHRuntime(
                profile_spec=self._profile_spec(source),
                dsh_home=root / "dsh-home",
                env={"ANTHROPIC_BASE_URL": "https://gateway.test", "ANTHROPIC_AUTH_TOKEN": "token"},
                dsh_executable=self._create_executable(root),
            )
            (source / "pnpm-workspace.yaml").unlink()
            with self.assertRaisesRegex(DSHProfileNotFoundError, "missing required assets"):
                runtime._synchronize_profile()

            (source / "pnpm-workspace.yaml").write_text("packages:\n  - .\n", encoding="utf-8")
            (source / "package.json").write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(DSHProfileNotFoundError, "dsh.profile.bundles"):
                runtime._synchronize_profile()

    def test_preflight_is_side_effect_free_and_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = self._create_profile_source(root)
            runtime = DSHRuntime(
                profile_spec=self._profile_spec(
                    source,
                    profile_id="project-context",
                    required_environment=(),
                ),
                dsh_home=root / "dsh-home",
                dsh_executable=self._create_executable(root),
            )

            readiness = runtime.preflight()

            self.assertTrue(readiness.ready)
            self.assertEqual(readiness.profile_identity, "project-context@test")
            self.assertFalse((root / "dsh-home").exists())

    def test_preflight_rejects_missing_profile_environment_without_creating_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = self._create_profile_source(root)
            runtime = DSHRuntime(
                profile_spec=self._profile_spec(source),
                dsh_home=root / "dsh-home",
                dsh_executable=self._create_executable(root),
            )

            with patch.dict(dsh_runtime.os.environ, {}, clear=True):
                readiness = runtime.preflight()

            self.assertFalse(readiness.ready)
            self.assertEqual(readiness.reason_code, "profile_environment_invalid")
            self.assertFalse((root / "dsh-home").exists())

    async def test_direct_executable_runs_with_isolated_profile_and_redacts_stderr(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runtime = self._runtime(root, self._create_executable(root))

            result = await runtime.run_agent_task("test task")

            self.assertEqual(result.output, "DSH stub completed")
            self.assertEqual(result.error, "[REDACTED]")
            self.assertEqual(result.metadata["dsh_executable"], str(runtime.dsh_executable))
            profile_dir = runtime._profile_dir_for(result.metadata["profile_fingerprint"])
            self.assertTrue(profile_dir.is_dir())
            self.assertEqual(runtime._redact("sensitive-token", runtime._build_env()), "[REDACTED]")

    async def test_metadata_is_digested_and_not_passed_through_argv_or_environment(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            arguments = root / "arguments.txt"
            executable = self._create_executable(
                root,
                "#!/bin/sh\nprintf '%s\\n' \"$@\" > " + shlex.quote(str(arguments)) + "\nprintf 'ok\\n'\n",
            )
            runtime = self._runtime(root, executable)

            result = await runtime.run_agent_task(
                "safe prompt",
                agent_id="agent-secret",
                project_id="project-secret",
                metadata={"context_snapshot": "snapshot-secret"},
            )

            child_arguments = arguments.read_text(encoding="utf-8")
            self.assertNotIn("agent-secret", child_arguments)
            self.assertNotIn("project-secret", child_arguments)
            self.assertNotIn("snapshot-secret", child_arguments)
            self.assertIn("context_context_snapshot_sha256", result.metadata)
            self.assertNotIn("context_snapshot", result.metadata)
            self.assertNotIn("snapshot-secret", result.metadata.values())

    async def test_nonzero_exit_redacts_gateway_token(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable = self._create_executable(
                root,
                "#!/bin/sh\nprintf '%s\\n' \"gateway token: $ANTHROPIC_AUTH_TOKEN\" >&2\nexit 7\n",
            )
            runtime = self._runtime(root, executable)

            with self.assertRaisesRegex(DSHExecutionError, "code 7") as context:
                await runtime.run_agent_task("test task")

            self.assertIn("[REDACTED]", str(context.exception))
            self.assertNotIn("sensitive-token", str(context.exception))

    async def test_rejects_task_larger_than_positional_argv_budget(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runtime = self._runtime(root, self._create_executable(root), max_task_bytes=4)

            with self.assertRaisesRegex(DSHExecutionError, "task is 5 bytes"):
                await runtime.run_agent_task("abcde")

    async def test_output_limit_terminates_process_group(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable = self._create_executable(root, "#!/bin/sh\nprintf '0123456789abcdef'\nsleep 5\n")
            runtime = self._runtime(
                root,
                executable,
                max_stdout_bytes=8,
                timeout=2,
                shutdown_grace_seconds=0.1,
            )

            with self.assertRaisesRegex(DSHExecutionError, "stdout exceeded"):
                await runtime.run_agent_task("test task")

    async def test_timeout_reaps_descendant_after_parent_exits(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            child_pid = root / "child-pid"
            executable = self._create_executable(
                root,
                "#!/bin/sh\n"
                "( trap '' TERM; while :; do sleep 1; done ) &\n"
                "printf '%s' \"$!\" > " + shlex.quote(str(child_pid)) + "\n"
                "exit 0\n",
            )
            runtime = self._runtime(
                root,
                executable,
                timeout=0.2,
                shutdown_grace_seconds=0.1,
            )

            with self.assertRaisesRegex(DSHExecutionError, "timed out"):
                await runtime.run_agent_task("test task")

            pid = int(child_pid.read_text(encoding="utf-8"))
            for _ in range(20):
                if not _pid_exists(pid):
                    break
                await asyncio.sleep(0.05)
            self.assertFalse(_pid_exists(pid), "DSH descendant survived process-group cleanup")

    async def test_cancellation_reaps_process_group(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            child_pid = root / "child-pid"
            executable = self._create_executable(
                root,
                "#!/bin/sh\n"
                "sleep 30 &\n"
                "printf '%s' \"$!\" > " + shlex.quote(str(child_pid)) + "\n"
                "wait\n",
            )
            runtime = self._runtime(root, executable, timeout=10, shutdown_grace_seconds=0.1)
            invocation = asyncio.create_task(runtime.run_agent_task("test task"))
            for _ in range(20):
                if child_pid.exists():
                    break
                await asyncio.sleep(0.02)
            invocation.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await invocation

            pid = int(child_pid.read_text(encoding="utf-8"))
            loop = asyncio.get_running_loop()
            deadline = loop.time() + 5
            while _pid_is_running(pid) and loop.time() < deadline:  # noqa: ASYNC110
                await asyncio.sleep(0.05)
            self.assertFalse(_pid_is_running(pid), "DSH descendant survived cancellation cleanup")

    async def test_clarify_retries_once_with_generic_host_repair_instruction(self) -> None:
        class FakeRuntime:
            tasks: list[str] = []

            def __init__(self, *args: object, **kwargs: object) -> None:
                pass

            async def run_agent_task(self, task: str) -> DSHExecutionResult:
                self.tasks.append(task)
                return DSHExecutionResult(output="```json\n{}\n```")

        from ecms.agent.ba import dsh_compat

        with patch.object(dsh_compat, "DSHRuntime", FakeRuntime):
            with self.assertRaisesRegex(DSHExecutionError, "single JSON object"):
                await dsh_compat._run_structured_stage(
                    "clarify",
                    "brief",
                    lambda output: _json_object("clarify", output),
                )

        self.assertEqual(len(FakeRuntime.tasks), 2)
        self.assertIn("preceding response failed host validation", FakeRuntime.tasks[1])
        self.assertNotIn("single JSON object", FakeRuntime.tasks[1])

    def test_json_object_rejects_non_object_values(self) -> None:
        with self.assertRaisesRegex(DSHExecutionError, "not list"):
            _json_object("finalize", "[]")


def _pid_is_running(pid: int) -> bool:
    """Return whether a Linux PID is still scheduled rather than a reaping zombie."""
    status_path = Path(f"/proc/{pid}/status")
    try:
        status = status_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return False
    return not any(line == "State:\tZ (zombie)" for line in status.splitlines())


def _pid_exists(pid: int) -> bool:
    """Return whether an asserted child PID is still present on Linux."""
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True


if __name__ == "__main__":
    unittest.main()

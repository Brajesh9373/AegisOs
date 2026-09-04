"""Profile-neutral Agent OS DSH runtime settings tests."""

from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from pydantic import ValidationError

from ecms.agent_os.profiles.contracts import ProfileExecutionBudget
from ecms.configuration.schemas.settings import AppSettings


class AgentOSDSHSettingsTests(unittest.TestCase):
    """Keep host-level DSH limits independent from any one agent profile."""

    def test_defaults_match_the_shared_profile_execution_budget(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            settings = AppSettings()
        budget = ProfileExecutionBudget()

        self.assertEqual(settings.agent_os_dsh_timeout_seconds, budget.timeout_seconds)
        self.assertEqual(
            settings.agent_os_dsh_shutdown_grace_seconds,
            budget.shutdown_grace_seconds,
        )
        self.assertEqual(
            settings.agent_os_dsh_profile_lock_timeout_seconds,
            budget.profile_lock_timeout_seconds,
        )
        self.assertEqual(settings.agent_os_dsh_max_task_bytes, budget.max_task_bytes)
        self.assertEqual(settings.agent_os_dsh_max_command_bytes, budget.max_command_bytes)
        self.assertEqual(settings.agent_os_dsh_max_stdout_bytes, budget.max_stdout_bytes)
        self.assertEqual(settings.agent_os_dsh_max_stderr_bytes, budget.max_stderr_bytes)

    def test_new_environment_name_wins_over_legacy_ba_alias(self) -> None:
        with patch.dict(
            os.environ,
            {
                "ECMS_AGENT_OS_DSH_TIMEOUT_SECONDS": "10",
                "ECMS_BA_DSH_TIMEOUT_SECONDS": "20",
            },
            clear=True,
        ):
            settings = AppSettings()

        self.assertEqual(settings.agent_os_dsh_timeout_seconds, 10)

    def test_legacy_ba_environment_alias_remains_accepted(self) -> None:
        with patch.dict(
            os.environ,
            {"ECMS_BA_DSH_TIMEOUT_SECONDS": "42"},
            clear=True,
        ):
            settings = AppSettings()

        self.assertEqual(settings.agent_os_dsh_timeout_seconds, 42)

    def test_direct_field_names_remain_accepted(self) -> None:
        settings = AppSettings(
            agent_os_dsh_max_task_bytes=32_768,
            agent_os_dsh_max_command_bytes=65_536,
            ba_prompt_max_bytes=32_768,
        )

        self.assertEqual(settings.agent_os_dsh_max_task_bytes, 32_768)
        self.assertEqual(settings.agent_os_dsh_max_command_bytes, 65_536)

    def test_command_budget_must_cover_task_budget(self) -> None:
        with self.assertRaisesRegex(
            ValidationError,
            "agent_os_dsh_max_command_bytes must be at least",
        ):
            AppSettings(
                agent_os_dsh_max_task_bytes=16_384,
                agent_os_dsh_max_command_bytes=8_192,
                ba_prompt_max_bytes=16_384,
            )

    def test_ba_prompt_budget_must_fit_the_shared_dsh_task_budget(self) -> None:
        with self.assertRaisesRegex(
            ValidationError,
            "ba_prompt_max_bytes must not exceed agent_os_dsh_max_task_bytes",
        ):
            AppSettings(
                agent_os_dsh_max_task_bytes=32_768,
                agent_os_dsh_max_command_bytes=65_536,
                ba_prompt_max_bytes=65_536,
            )

    def test_settings_do_not_select_or_activate_a_profile(self) -> None:
        agent_os_fields = set(AppSettings.model_fields)

        self.assertNotIn("ba_dsh_profile", agent_os_fields)
        self.assertFalse(any(field.endswith("_profile") for field in agent_os_fields))


if __name__ == "__main__":
    unittest.main()

"""Regression coverage for Anthropic-compatible BA repair turns."""

from __future__ import annotations

import copy
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from ecms.agent.ba import agent


class FakeLlm:
    def __init__(self, payloads: list[str]) -> None:
        self.payloads = iter(payloads)
        self.calls: list[list[dict]] = []

    async def chat(self, *, messages: list[dict], **kwargs):
        self.calls.append(copy.deepcopy(messages))
        tool_call = SimpleNamespace(
            id=f"call-{len(self.calls)}",
            function=SimpleNamespace(arguments=next(self.payloads)),
        )
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(tool_calls=[tool_call]))]
        )


class BARepairMessageTests(unittest.IsolatedAsyncioTestCase):
    async def test_finalize_repair_turn_uses_empty_assistant_content(self) -> None:
        valid = agent._fallback_requirements("Create an invoice approval workspace.").model_dump(
            mode="json"
        )
        llm = FakeLlm([json.dumps({"projectName": "Incomplete"}), json.dumps(valid)])

        async def get_client(*args, **kwargs):
            return llm

        with patch.object(agent, "get_ba_llm_client", get_client):
            requirements = await agent.finalize(
                "Create an invoice approval workspace.",
                [{"role": "user", "content": "Proceed."}],
            )

        self.assertEqual(requirements.project_name, valid["project_name"])
        self.assertEqual(len(llm.calls), 2)
        repair_history = llm.calls[1]
        repair_tool_turn = next(
            message
            for message in repair_history
            if message["role"] == "assistant" and message.get("tool_calls")
        )
        self.assertEqual(repair_tool_turn["content"], "")
        self.assertNotIn(None, [message.get("content") for message in repair_history])

    async def test_design_team_repair_turn_uses_empty_assistant_content(self) -> None:
        llm = FakeLlm(["{}", "{}"])
        expected_team = SimpleNamespace(key="team")

        async def get_client(*args, **kwargs):
            return llm

        with (
            patch.object(agent, "get_ba_llm_client", get_client),
            patch.object(
                agent.AgentTeam,
                "validate_payload",
                side_effect=[ValueError("invalid team"), expected_team],
            ),
        ):
            team = await agent.design_team(
                requirements={"projectName": "Example"},
                conversation=[],
                model_ids=["glm-5"],
                tool_names=["read_file"],
            )

        self.assertIs(team, expected_team)
        self.assertEqual(len(llm.calls), 2)
        repair_history = llm.calls[1]
        repair_tool_turn = next(
            message
            for message in repair_history
            if message["role"] == "assistant" and message.get("tool_calls")
        )
        self.assertEqual(repair_tool_turn["content"], "")


if __name__ == "__main__":
    unittest.main()

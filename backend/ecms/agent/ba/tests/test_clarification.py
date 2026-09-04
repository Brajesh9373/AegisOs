import json
from types import SimpleNamespace

import pytest

from ecms.agent.ba.agent import _parse_clarification
from ecms.agent.ba.prompts import (
    CLARIFICATION_CATEGORIES,
    CLARIFICATION_TOOL,
    build_clarify_prompt,
    build_reply_prompt,
)


def _response(payload: dict):
    call = SimpleNamespace(
        function=SimpleNamespace(arguments=json.dumps(payload)),
    )
    message = SimpleNamespace(tool_calls=[call])
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def test_clarification_categories_match_product_contract() -> None:
    assert CLARIFICATION_CATEGORIES == {
        "background": "Background & Why It Is Needed",
        "pain_points": "Current Pain Points",
        "assumptions": "Assumptions",
        "architectural_depth": "Architectural Depth",
        "execution_stages": "Execution Stages",
        "timelines": "Timelines",
    }
    category_schema = CLARIFICATION_TOOL["function"]["parameters"]["properties"]["category"]
    assert category_schema["enum"] == list(CLARIFICATION_CATEGORIES)


def test_parse_clarification_adds_canonical_label() -> None:
    turn = _parse_clarification(
        _response(
            {
                "category": "pain_points",
                "questions_markdown": "- Where does the current process fail most often?",
            }
        )
    )

    assert turn == {
        "category": "pain_points",
        "category_label": "Current Pain Points",
        "content": "- Where does the current process fail most often?",
    }


@pytest.mark.parametrize(
    "payload",
    [
        {"category": "scope", "questions_markdown": "- What is in scope?"},
        {"category": "background", "questions_markdown": ""},
    ],
)
def test_parse_clarification_rejects_invalid_turn(payload: dict) -> None:
    with pytest.raises(ValueError):
        _parse_clarification(_response(payload))


def test_initial_prompt_requires_one_category_without_heading() -> None:
    prompt = build_clarify_prompt("Build an employee portal.")

    assert "single most useful category" in prompt
    assert "none may belong to another category" in prompt
    assert "do not include the category heading" in prompt


def test_follow_up_prompt_preserves_active_category_context() -> None:
    prompt = build_reply_prompt(
        "Build an employee portal.",
        [
            {
                "role": "assistant",
                "content": "Why is this needed?",
                "category": "background",
            },
            {"role": "user", "content": "To reduce HR email volume."},
        ],
        "To reduce HR email volume.",
        {"dimensions": []},
    )

    assert "CURRENT CLARIFICATION CATEGORY: background" in prompt
    assert "never mix categories" in prompt

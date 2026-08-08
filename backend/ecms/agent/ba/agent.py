"""BA agent core — the three staged LLM generations.

Each function is a single structured generation against the resolved BA model
(temperature 0). `finalize` uses function-calling for guaranteed structure plus
a validate/repair loop: if the emitted object fails the fixed-taxonomy schema,
the agent re-asks once with the validation error before giving up.

All LLM calls go through BaLlmClient (timeout, retry, circuit breaker).
"""

from __future__ import annotations

import json
import logging

from pydantic import ValidationError

from ecms.agent.ba.llm_client import get_ba_llm_client
from ecms.agent.ba.prompts import (
    ASSESS_TOOL,
    CLARIFICATION_CATEGORIES,
    CLARIFICATION_TOOL,
    FINALIZE_TOOL,
    build_assess_prompt,
    build_clarify_prompt,
    build_finalize_prompt,
    build_reply_prompt,
    build_system_prompt,
    build_team_prompt,
    build_team_tool,
    build_understand_prompt,
)
from ecms.agent.ba.schema import FinalizedRequirements
from ecms.agent.ba.team_schema import AgentTeam

logger = logging.getLogger("ecms.ba.agent")


def _parse_clarification(response) -> dict[str, str]:
    tool_calls = response.choices[0].message.tool_calls or []
    if not tool_calls:
        raise ValueError("BA clarification did not emit a structured turn")
    payload = json.loads(tool_calls[0].function.arguments or "{}")
    category = payload.get("category")
    questions = str(payload.get("questions_markdown") or "").strip()
    if category not in CLARIFICATION_CATEGORIES or not questions:
        raise ValueError("BA clarification emitted an invalid category or empty questions")
    return {
        "category": category,
        "category_label": CLARIFICATION_CATEGORIES[category],
        "content": questions,
    }


async def retrieve_knowledge(source_text: str, conversation: list[dict] | None = None) -> str:
    """Retrieve relevant knowledge for a project. Returns empty string on failure."""
    try:
        from ecms.agent.ba.knowledge.retrieval import retrieve_for_project
        return await retrieve_for_project(source_text, conversation)
    except Exception as exc:
        logger.warning("[ba.agent] knowledge retrieval failed, proceeding without: %s", exc)
        return ""


async def understand(source_text: str, knowledge_context: str = "") -> str:
    """Stage 1 — the 'What I understood' recap message (Markdown)."""
    llm = await get_ba_llm_client()
    resp = await llm.chat(
        messages=[
            {"role": "system", "content": build_system_prompt(knowledge_context)},
            {"role": "user", "content": build_understand_prompt(source_text)},
        ],
        temperature=0.0,
        max_tokens=1600,
    )
    return (resp.choices[0].message.content or "").strip()


async def clarify(source_text: str, knowledge_context: str = "") -> dict[str, str]:
    """Stage 2 — one structured, category-specific question batch."""
    llm = await get_ba_llm_client()
    resp = await llm.chat(
        messages=[
            {"role": "system", "content": build_system_prompt(knowledge_context)},
            {"role": "user", "content": build_clarify_prompt(source_text)},
        ],
        tools=[CLARIFICATION_TOOL],
        tool_choice={"type": "function", "function": {"name": "emit_clarification"}},
        temperature=0.0,
        max_tokens=4000,
    )
    return _parse_clarification(resp)


async def assess_coverage(source_text: str, conversation: list[dict], knowledge_context: str = "") -> dict:
    """Score every requirement dimension across the full conversation."""
    llm = await get_ba_llm_client()
    try:
        resp = await llm.chat(
            messages=[
                {"role": "system", "content": build_system_prompt(knowledge_context)},
                {"role": "user", "content": build_assess_prompt(source_text, conversation)},
            ],
            tools=[ASSESS_TOOL],
            tool_choice={"type": "function", "function": {"name": "assess_coverage"}},
            temperature=0.0,
            max_tokens=2000,
        )
    except Exception as exc:
        logger.warning("[ba.assess_coverage] LLM call failed, returning empty coverage: %s", exc)
        return {"dimensions": [], "critical_ready": False, "open_questions": []}
    tool_calls = resp.choices[0].message.tool_calls or []
    if not tool_calls:
        return {"dimensions": [], "critical_ready": False, "open_questions": []}
    try:
        return json.loads(tool_calls[0].function.arguments or "{}")
    except json.JSONDecodeError:
        return {"dimensions": [], "critical_ready": False, "open_questions": []}


async def chat_reply(
    source_text: str,
    conversation: list[dict],
    user_message: str,
    knowledge_context: str = "",
) -> dict[str, str]:
    """Chat turn — a coverage-driven reply."""
    coverage = await assess_coverage(source_text, conversation, knowledge_context)
    llm = await get_ba_llm_client()
    resp = await llm.chat(
        messages=[
            {"role": "system", "content": build_system_prompt(knowledge_context)},
            {"role": "user", "content": build_reply_prompt(source_text, conversation, user_message, coverage)},
        ],
        tools=[CLARIFICATION_TOOL],
        tool_choice={"type": "function", "function": {"name": "emit_clarification"}},
        temperature=0.0,
        max_tokens=2200,
    )
    return _parse_clarification(resp)


async def finalize(source_text: str, conversation: list[dict], knowledge_context: str = "") -> FinalizedRequirements:
    """Stage 3 — the FinalizedRequirements object (validated / repaired)."""
    from ecms.agent.ba.llm_client import LlmCallOpts

    llm = await get_ba_llm_client(opts=LlmCallOpts.for_finalize())
    messages = [
        {"role": "system", "content": build_system_prompt(knowledge_context)},
        {"role": "user", "content": build_finalize_prompt(source_text, conversation)},
    ]

    last_error: str | None = None
    for attempt in range(2):
        if last_error:
            messages.append({
                "role": "user",
                "content": (
                    f"Your previous emit_requirements call was invalid: {last_error}. "
                    "Call emit_requirements again with the corrected object. The "
                    "governance/guardrails/infrastructure labels must match exactly, "
                    "and phases must start with Discovery & Requirements Baseline "
                    "followed by descriptions that start with Depends on <previous phase name>:."
                ),
            })
        resp = await llm.chat(
            messages=messages,
            tools=[FINALIZE_TOOL],
            tool_choice={"type": "function", "function": {"name": "emit_requirements"}},
            temperature=0.0,
            max_tokens=6000,
        )
        msg = resp.choices[0].message
        tool_calls = msg.tool_calls or []
        if not tool_calls:
            last_error = "no emit_requirements tool call was made"
            logger.warning("[ba.finalize] attempt %d: no tool call", attempt)
            continue
        raw = tool_calls[0].function.arguments or "{}"
        try:
            data = json.loads(raw)
            return FinalizedRequirements.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as exc:
            last_error = str(exc)
            logger.warning("[ba.finalize] attempt %d validation failed: %s", attempt, exc)
            messages.append({
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "id": tool_calls[0].id,
                    "type": "function",
                    "function": {"name": "emit_requirements", "arguments": raw},
                }],
            })
            messages.append({
                "role": "tool",
                "tool_call_id": tool_calls[0].id,
                "content": f"validation error: {last_error}",
            })

    raise ValueError(f"BA finalize failed after retries: {last_error}")


async def design_team(
    requirements: dict,
    conversation: list[dict],
    model_ids: list[str],
    tool_names: list[str],
    knowledge_context: str = "",
    org_roster: list[dict] | None = None,
) -> AgentTeam:
    """Stage 4 — design the per-project agent org chart (validated / repaired)."""
    llm = await get_ba_llm_client()
    team_tool = build_team_tool(model_ids, tool_names)
    allowed_models = tuple(model_ids)
    allowed_tools = tuple(tool_names)
    allowed_org_member_ids = tuple(
        str(member["id"])
        for member in (org_roster or [])
        if member.get("id")
    )
    messages = [
        {"role": "system", "content": build_system_prompt(knowledge_context)},
        {"role": "user", "content": build_team_prompt(requirements, conversation, org_roster=org_roster)},
    ]

    last_error: str | None = None
    for attempt in range(2):
        if last_error:
            messages.append({
                "role": "user",
                "content": (
                    f"Your previous emit_team call was invalid: {last_error}. "
                    "Call emit_team again with the corrected org chart. Exactly one "
                    "delivery_manager root (reports_to=null); every reports_to must "
                    "reference an existing key; only management roles may have reports."
                ),
            })
        resp = await llm.chat(
            messages=messages,
            tools=[team_tool],
            tool_choice={"type": "function", "function": {"name": "emit_team"}},
            temperature=0.0,
            max_tokens=6000,
        )
        msg = resp.choices[0].message
        tool_calls = msg.tool_calls or []
        if not tool_calls:
            last_error = "no emit_team tool call was made"
            logger.warning("[ba.design_team] attempt %d: no tool call", attempt)
            continue
        raw = tool_calls[0].function.arguments or "{}"
        try:
            data = json.loads(raw)
            return AgentTeam.validate_payload(
                data,
                allowed_models,
                allowed_tools,
                allowed_org_member_ids,
            )
        except (json.JSONDecodeError, ValidationError, ValueError) as exc:
            last_error = str(exc)
            logger.warning("[ba.design_team] attempt %d validation failed: %s", attempt, exc)
            messages.append({
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "id": tool_calls[0].id,
                    "type": "function",
                    "function": {"name": "emit_team", "arguments": raw},
                }],
            })
            messages.append({
                "role": "tool",
                "tool_call_id": tool_calls[0].id,
                "content": f"validation error: {last_error}",
            })

    raise ValueError(f"BA design_team failed after retries: {last_error}")

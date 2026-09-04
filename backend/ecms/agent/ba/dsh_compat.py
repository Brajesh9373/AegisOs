"""Temporary BA compatibility helpers built on the profile-neutral DSH runtime.

Production discovery uses the scoped cognition service. These adapters preserve
legacy callers while keeping BA prompt prose and output validation out of the
shared subprocess kernel.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from ecms.agent.ba.dsh_profile import business_analyst_dsh_profile_spec
from ecms.agent.dsh_runtime import DSHExecutionError, DSHRuntime

__all__ = [
    "_json_object",
    "_run_structured_stage",
    "ba_clarify",
    "ba_design_team",
    "ba_finalize",
    "ba_understand",
]

logger = logging.getLogger("ecms.agent.ba.dsh_compat")


def _runtime(**kwargs: Any) -> DSHRuntime:
    """Create the BA profile runtime without embedding BA policy in the kernel."""
    return DSHRuntime(profile_spec=business_analyst_dsh_profile_spec(), **kwargs)


def _json_object(stage: str, output: str) -> dict[str, Any]:
    """Parse the single JSON object required by structured BA stages."""
    try:
        value = json.loads(output)
    except json.JSONDecodeError as exc:
        raise DSHExecutionError(
            f"DSH BA {stage} stage did not return a single JSON object: {exc.msg}"
        ) from exc
    if not isinstance(value, dict):
        raise DSHExecutionError(
            f"DSH BA {stage} stage must return a JSON object, not {type(value).__name__}."
        )
    return value


async def ba_understand(source_text: str, **kwargs: Any) -> str:
    """Run the BA understand stage through the BA-owned DSH profile."""
    result = await _runtime(**kwargs).run_agent_task(
        "Stage 1 — Understand the following project brief. Return only the requested "
        f"recap.\n\nPROJECT BRIEF:\n{source_text}"
    )
    if not result.output:
        raise DSHExecutionError("DSH BA understand stage returned an empty response.")
    return result.output


async def _run_structured_stage(
    stage: str,
    task: str,
    validator: Any,
    **kwargs: Any,
) -> Any:
    """Run a DSH JSON stage with one generic corrective retry."""
    runtime = _runtime(**kwargs)
    validation_error: DSHExecutionError | None = None
    for attempt in range(2):
        repair_instruction = ""
        if validation_error is not None:
            repair_instruction = (
                "\n\nThe preceding response failed host validation. Generate a new JSON object "
                "that follows the required contract exactly. Return JSON only; do not include "
                "Markdown, commentary, or an explanation of the correction."
            )
        result = await runtime.run_agent_task(task + repair_instruction)
        try:
            return validator(result.output)
        except DSHExecutionError as exc:
            validation_error = exc
            logger.warning(
                "[DSH] BA %s output failed strict validation on attempt %d", stage, attempt + 1
            )

    assert validation_error is not None
    raise validation_error


async def ba_clarify(source_text: str, **kwargs: Any) -> dict[str, str]:
    """Run and strictly validate the BA clarification stage through DSH."""
    from ecms.agent.ba.prompts import CLARIFICATION_CATEGORIES

    supported_categories = ", ".join(CLARIFICATION_CATEGORIES)
    task = (
        "Stage 2 — Clarify the following project brief. Return only one JSON object, "
        "with no Markdown fences or extra text, in exactly this shape: "
        '{"category":"one supported value","questions_markdown":"non-empty questions"}. '
        f"category must be exactly one of: {supported_categories}. "
        "questions_markdown must be a non-empty string of focused questions.\n\n"
        f"PROJECT BRIEF:\n{source_text}"
    )

    def validate(output: str) -> dict[str, str]:
        payload = _json_object("clarify", output)
        category = payload.get("category")
        questions = str(payload.get("questions_markdown") or "").strip()
        if category not in CLARIFICATION_CATEGORIES or not questions:
            raise DSHExecutionError(
                "DSH BA clarify stage returned invalid fields: "
                f"category={category!r}, questions_markdown_length={len(questions)}. "
                f"category must be one of: {supported_categories}."
            )
        return {
            "category": category,
            "category_label": CLARIFICATION_CATEGORIES[category],
            "content": questions,
        }

    return await _run_structured_stage("clarify", task, validate, **kwargs)


async def ba_finalize(
    source_text: str,
    conversation: list[dict[str, Any]],
    **kwargs: Any,
) -> dict[str, Any]:
    """Run and validate a ``FinalizedRequirements`` package through DSH."""
    from ecms.agent.ba.schema import FinalizedRequirements

    task = (
        "Stage 3 — Finalize requirements. Return only the exact JSON object required "
        "by the system prompt; do not use Markdown fences.\n\n"
        f"PROJECT BRIEF:\n{source_text}\n\n"
        f"DISCOVERY CONVERSATION:\n{json.dumps(conversation, ensure_ascii=False)}"
    )

    def validate(output: str) -> dict[str, Any]:
        payload = _json_object("finalize", output)
        try:
            requirements = FinalizedRequirements.model_validate(payload)
        except Exception as exc:
            raise DSHExecutionError(
                "DSH BA finalize stage returned an invalid FinalizedRequirements object: "
                f"{exc}"
            ) from exc
        return requirements.to_frontend()

    return await _run_structured_stage("finalize", task, validate, **kwargs)


async def ba_design_team(
    requirements: dict[str, Any],
    model_ids: list[str],
    tool_names: list[str],
    org_member_ids: list[str] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Run and validate an ``AgentTeam`` design through DSH."""
    from ecms.agent.ba.team_schema import AgentTeam

    task = (
        "Stage 4 — Design the delivery team. Return only the exact JSON object required "
        "by the system prompt; do not use Markdown fences.\n\n"
        f"FINALIZED REQUIREMENTS:\n{json.dumps(requirements, ensure_ascii=False)}\n\n"
        f"AVAILABLE MODELS:\n{json.dumps(model_ids)}\n\n"
        f"AVAILABLE TOOLS:\n{json.dumps(tool_names)}\n\n"
        f"ORGANIZATION MEMBER IDS:\n{json.dumps(org_member_ids or [])}"
    )

    def validate(output: str) -> dict[str, Any]:
        payload = _json_object("design-team", output)
        try:
            team = AgentTeam.validate_payload(
                payload,
                allowed_models=tuple(model_ids),
                allowed_tools=tuple(tool_names),
                allowed_org_member_ids=tuple(org_member_ids or []),
            )
        except Exception as exc:
            raise DSHExecutionError(
                f"DSH BA design-team stage returned an invalid AgentTeam object: {exc}"
            ) from exc
        return team.model_dump()

    return await _run_structured_stage("design-team", task, validate, **kwargs)

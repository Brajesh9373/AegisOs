"""Business Analyst cognition orchestration over an isolated stage executor."""

from __future__ import annotations

import json
import logging
from collections.abc import Mapping, Sequence
from typing import Any, cast

from ecms.agent.ba.cognition.contracts import (
    BAExecutionContext,
    BAStage,
    BAStageExecutor,
    BAStageInvocation,
    BAStageResult,
    CognitionContextProvider,
    DiscoveryMemoryWriter,
    JSONValue,
    PromptBudget,
    PromptMessage,
)
from ecms.agent.ba.cognition.renderer import BAStagePromptRenderer
from ecms.agent.ba.prompts import CLARIFICATION_CATEGORIES
from ecms.agent.ba.schema import FinalizedRequirements
from ecms.agent.ba.team_schema import AgentTeam

__all__ = ["BACognitionService", "BAStageValidationError", "NoopDiscoveryMemoryWriter"]

logger = logging.getLogger("ecms.agent.ba.cognition")


class BAStageValidationError(ValueError):
    """Raised when an executor response cannot satisfy a fixed BA stage contract."""


class NoopDiscoveryMemoryWriter:
    """Explicit test-only writer for isolated cognition service composition."""

    async def record(self, result: BAStageResult) -> None:
        """Discard a test result without claiming durable write-back occurred."""
        del result


class BACognitionService:
    """Execute a BA stage against exactly one immutable host-built context snapshot."""

    def __init__(
        self,
        *,
        provider: CognitionContextProvider,
        executor: BAStageExecutor,
        writer: DiscoveryMemoryWriter | None = None,
        renderer: BAStagePromptRenderer | None = None,
        budget: PromptBudget | None = None,
    ) -> None:
        """Initialize the service with scoped context and DSH execution boundaries."""
        self._provider = provider
        self._executor = executor
        self._writer = writer
        self._renderer = renderer or BAStagePromptRenderer()
        self._budget = budget or PromptBudget()

    async def execute(
        self,
        *,
        stage: BAStage,
        context: BAExecutionContext,
        source_text: str,
        conversation: Sequence[Mapping[str, object]] | tuple[PromptMessage, ...] = (),
        model_ids: tuple[str, ...] = (),
        tool_names: tuple[str, ...] = (),
        organization_member_ids: tuple[str, ...] = (),
    ) -> BAStageResult:
        """Build context once, execute at most twice, validate, then durably record.

        The same packet object is reused for the single corrective retry. Therefore a
        retrieval cache change, policy change, or source mutation cannot silently
        alter evidence between an invalid response and its correction.
        """
        messages = _normalize_messages(conversation)
        packet = await self._provider.build_packet(
            context,
            source_text=source_text,
            conversation=messages,
            budget=self._budget,
        )
        validation_error: BAStageValidationError | None = None
        for attempt in range(1, 3):
            prompt = self._renderer.render(
                stage=stage,
                packet=packet,
                budget=self._budget,
                repair_required=validation_error is not None,
                model_ids=model_ids,
                tool_names=tool_names,
                organization_member_ids=organization_member_ids,
            )
            execution = await self._executor.execute(
                BAStageInvocation(
                    stage=stage,
                    packet=packet,
                    rendered_prompt=prompt,
                    attempt=attempt,
                    model_ids=model_ids,
                    tool_names=tool_names,
                    organization_member_ids=organization_member_ids,
                )
            )
            try:
                output = _validate_stage(
                    stage,
                    execution.output,
                    model_ids=model_ids,
                    tool_names=tool_names,
                    organization_member_ids=organization_member_ids,
                )
            except BAStageValidationError as exc:
                validation_error = exc
                logger.warning(
                    "BA stage output failed validation",
                    extra={
                        "stage": stage.value,
                        "attempt": attempt,
                        "context_snapshot": packet.snapshot_hash,
                    },
                )
                continue
            result = BAStageResult(
                stage=stage,
                packet=packet,
                output=output,
                execution=execution,
                validation_attempts=attempt,
            )
            if self._writer is not None:
                await self._writer.record(result)
            return result
        assert validation_error is not None
        raise validation_error


def _normalize_messages(
    conversation: Sequence[Mapping[str, object]] | tuple[PromptMessage, ...],
) -> tuple[PromptMessage, ...]:
    """Normalize persisted discovery messages into immutable untrusted prompt input."""
    if isinstance(conversation, tuple) and all(
        isinstance(message, PromptMessage) for message in conversation
    ):
        return conversation
    normalized: list[PromptMessage] = []
    for message in conversation:
        role = str(message.get("role", "user")).strip() or "user"
        content = str(message.get("content", ""))
        normalized.append(PromptMessage(role=role, content=content))
    return tuple(normalized)


def _json_object(stage: BAStage, output: str) -> dict[str, object]:
    """Parse the exact JSON object required by a structured stage."""
    try:
        value = json.loads(output)
    except json.JSONDecodeError as exc:
        raise BAStageValidationError(
            f"BA {stage.value} stage did not return a single JSON object."
        ) from exc
    if not isinstance(value, dict):
        raise BAStageValidationError(f"BA {stage.value} stage must return a JSON object.")
    return cast(dict[str, object], value)


def _validate_stage(
    stage: BAStage,
    output: str,
    *,
    model_ids: tuple[str, ...],
    tool_names: tuple[str, ...],
    organization_member_ids: tuple[str, ...],
) -> JSONValue:
    """Apply the current BA schema contract without accepting malformed output."""
    if stage is BAStage.UNDERSTAND:
        value = output.strip()
        if not value:
            raise BAStageValidationError("BA understand stage returned an empty response.")
        return value
    if stage is BAStage.CLARIFY:
        payload = _json_object(stage, output)
        category = payload.get("category")
        questions = str(payload.get("questions_markdown") or "").strip()
        if not isinstance(category, str) or category not in CLARIFICATION_CATEGORIES or not questions:
            raise BAStageValidationError("BA clarify stage returned an invalid category or question set.")
        return {
            "category": category,
            "category_label": CLARIFICATION_CATEGORIES[category],
            "content": questions,
        }
    if stage is BAStage.FINALIZE:
        payload = _json_object(stage, output)
        try:
            return cast(JSONValue, FinalizedRequirements.model_validate(payload).to_frontend())
        except Exception as exc:
            raise BAStageValidationError(
                "BA finalize stage returned an invalid FinalizedRequirements object."
            ) from exc
    payload = _json_object(stage, output)
    try:
        return cast(
            JSONValue,
            AgentTeam.validate_payload(
                payload,
                allowed_models=model_ids,
                allowed_tools=tool_names,
                allowed_org_member_ids=organization_member_ids,
            ).model_dump(),
        )
    except Exception as exc:
        raise BAStageValidationError("BA design-team stage returned an invalid AgentTeam object.") from exc

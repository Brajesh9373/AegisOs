"""Orchestrator tool — spawns sub-agents for parallel task execution.

Registered as a tool that the main AgentLoop can call to delegate work
to independent sub-agents with their own 50-iteration budget.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from legacy_ecms.config import get_settings

logger = logging.getLogger("ecms.orchestrator")

# Global callback for SSE events
_sse_emitter = None


def set_sse_emitter(emitter):
    """Register the SSE event emitter so tools can push progress."""
    global _sse_emitter
    _sse_emitter = emitter


async def spawn_subagent(task_id: str, title: str, description: str, instructions: str) -> str:
    """Spawn a sub-agent to execute a task independently.

    The sub-agent gets a fresh 50-iteration budget and runs the task
    instructions as its prompt. Returns the sub-agent's answer.

    Args:
        task_id: Unique task identifier (e.g., "1", "2")
        title: Short display name for the task
        description: What this task is about
        instructions: The detailed prompt for the sub-agent to execute
    """
    from ecms.agent.loop import AgentLoop
    from ecms.persistence.database.rest_session import db_session

    settings = get_settings()
    logger.info("[SUB-%s] START | %s | %s", task_id, title, instructions[:100])

    if _sse_emitter:
        _sse_emitter({"type": "task_start", "id": str(task_id), "title": title})

    try:
        loop = AgentLoop(
            f"task-{task_id}-{title[:20]}",
            model=settings.llm_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            agent_id=str(task_id),
        )
        answer, trace = await asyncio.wait_for(
            loop.run(instructions),
            timeout=180.0,
        )

        logger.info("[SUB-%s] DONE | %d chars", task_id, len(answer))
        if _sse_emitter:
            _sse_emitter({"type": "task_done", "id": str(task_id), "title": title, "result_preview": answer[:200]})

        return f"Task '{title}' completed. Result:\n{answer}"

    except asyncio.TimeoutError:
        logger.warning("[SUB-%s] TIMEOUT", task_id)
        if _sse_emitter:
            _sse_emitter({"type": "task_failed", "id": str(task_id), "title": title, "error": "timed_out"})
        return f"Task '{title}' timed out after 180 seconds. Provide partial findings or skip this task."

    except Exception as e:
        logger.error("[SUB-%s] FAILED: %s", task_id, e)
        if _sse_emitter:
            _sse_emitter({"type": "task_failed", "id": str(task_id), "title": title, "error": str(e)})
        return f"Task '{title}' failed: {e}"


# Tool definition for the LLM to call
SPAWN_SUBAGENT_TOOL = {
    "type": "function",
    "function": {
        "name": "spawn_subagent",
        "description": (
            "Spawn an independent AI sub-agent to execute a specific task. "
            "Use this to parallelize work — each sub-agent gets its own budget. "
            "Provide clear, detailed instructions so the sub-agent knows exactly what to do and what format to return results in. "
            "After all sub-agents complete, compile their results into a final answer."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "Unique task number (e.g., '1', '2', '3').",
                },
                "title": {
                    "type": "string",
                    "description": "Short display name for the task (used in UI progress).",
                },
                "description": {
                    "type": "string",
                    "description": "Brief one-line description of what this task does.",
                },
                "instructions": {
                    "type": "string",
                    "description": (
                        "Complete, detailed instructions for the sub-agent. Include: "
                        "1) What to investigate/analyze, "
                        "2) What specific information to find, "
                        "3) What format to return results in, "
                        "4) Any constraints or boundaries."
                    ),
                },
            },
            "required": ["task_id", "title", "description", "instructions"],
        },
    },
}

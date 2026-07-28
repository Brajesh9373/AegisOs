"""Agentic ReAct loop — the agent owns memory, tools are its instruments.

Replaces the pre-injection pipeline. The LLM decides which tools to call,
reads results, and iterates until it has enough context to respond.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import platform as _platform
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from openai import AsyncOpenAI

from legacy_ecms.config import get_settings
from ecms.agent.conversation import Conversation
from ecms.agent.session_context import SessionContext
from ecms.agent.tools import (
    TOOL_DEFINITIONS,
    invoke_tool,
    set_agent_context,
    get_working_memory,
    set_cc_context,
    get_effective_tools,
    CC_TOOL_DEFINITIONS,
)
from ecms.agent.commandcode_tools import ToolContext as CCToolContext
from ecms.agent.tool_capture import capture_tool_result
from ecms.agent.working_memory import WorkingMemory
from ecms.memory.system_prompt import AGENTIC_SYSTEM_PROMPT

logger = logging.getLogger("ecms.agent")


# ── Proactive context builders ───────────────────────────────────────

_SKILLS_CACHE: str | None = None

def _load_skills_context() -> str:
    """Load bundled skills from disk and return their descriptions."""
    global _SKILLS_CACHE
    if _SKILLS_CACHE is not None:
        return _SKILLS_CACHE

    skill_paths = [
        Path("/app/commandcode/skills"),
        Path("/commandcode/skills"),
        Path.cwd() / "commandcode" / "skills",
    ]

    skills_found: list[str] = []
    for root in skill_paths:
        if not root.is_dir():
            continue
        for skill_dir in sorted(root.iterdir()):
            if not skill_dir.is_dir():
                continue
            skill_file = skill_dir / "SKILL.md"
            if not skill_file.is_file():
                continue
            try:
                content = skill_file.read_text(encoding="utf-8", errors="replace")
                # Extract frontmatter name and description
                name = skill_dir.name
                desc = ""
                in_frontmatter = False
                for line in content.split("\n"):
                    line = line.strip()
                    if line == "---":
                        if not in_frontmatter:
                            in_frontmatter = True
                            continue
                        else:
                            break
                    if in_frontmatter:
                        if line.startswith("name:"):
                            name = line.split(":", 1)[1].strip()
                        elif line.startswith("description:") and not desc:
                            desc = line.split(":", 1)[1].strip().strip('"').strip("'")
                skills_found.append(f"- **{name}**: {desc}" if desc else f"- **{name}**: {skill_dir.name}")
            except Exception:
                skills_found.append(f"- {skill_dir.name}")

    if not skills_found:
        _SKILLS_CACHE = "No skills loaded."
    else:
        _SKILLS_CACHE = "\n".join(skills_found)

    return _SKILLS_CACHE


def _git_branch() -> str:
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True, text=True, timeout=5, cwd="/workspace",
        )
        return result.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def _git_status() -> str:
    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            capture_output=True, text=True, timeout=5, cwd="/workspace",
        )
        lines = result.stdout.strip().split("\n")
        modified = sum(1 for l in lines if l.startswith("M ") or l.startswith(" M"))
        added = sum(1 for l in lines if l.startswith("??"))
        deleted = sum(1 for l in lines if l.startswith("D ") or l.startswith(" D"))
        return f"M {modified}, A {added}, D {deleted}, {len(lines)} total"
    except Exception:
        return "unavailable"


def _build_environment_block(session_id: str, plan_mode: bool) -> str:
    """Build <context_environment> with live system data."""
    lines = [
        f"Working directory: /workspace",
        f"Date: {datetime.now(timezone.utc).isoformat()}",
        f"Platform: {_platform.system()} {_platform.release()}",
        f"Git branch: {_git_branch()}",
        f"Git status: {_git_status()}",
        f"Workspace roots: /workspace, /app",
        f"Session: {session_id[:8]}",
        f"Plan mode: {'ON' if plan_mode else 'OFF'}",
    ]
    return "<context_environment>\n" + "\n".join(lines) + "\n</context_environment>"


def _build_skills_block() -> str:
    """Build <context_skills> with loaded skill descriptions."""
    return "<context_skills>\n" + _load_skills_context() + "\n</context_skills>"


def _build_tools_block(tool_defs: list[dict]) -> str:
    """Build <context_tools> with tool names and schemas."""
    lines = [f"{len(tool_defs)} tools available:"]
    for t in tool_defs:
        name = t["function"]["name"]
        desc = t["function"]["description"].replace("\n", " ")[:120]
        params = t["function"]["parameters"].get("required", [])
        param_str = ", ".join(params) if params else "none"
        lines.append(f"- {name}({param_str}): {desc}")
    return "<context_tools>\n" + "\n".join(lines) + "\n</context_tools>"


# ── AgentLoop ────────────────────────────────────────────────────────


@dataclass
class AgentTrace:
    """Captured trace of every agent action for visibility."""
    session_id: str
    trace_id: str
    started_at: str = ""
    steps: list[dict] = field(default_factory=list)
    total_tool_calls: int = 0
    total_llm_calls: int = 0
    total_ms: float = 0.0

    def add_step(self, kind: str, detail: str, latency_ms: float = 0.0,
                 data: dict | None = None) -> None:
        step: dict = {"kind": kind, "detail": detail, "ms": round(latency_ms, 1)}
        if data:
            step["data"] = data
        self.steps.append(step)
        if kind == "tool_call":
            self.total_tool_calls += 1
        elif kind == "llm_call" or kind == "thinking":
            self.total_llm_calls += 1

    def to_dict(self) -> dict:
        return {
            "trace_id": self.trace_id,
            "session_id": self.session_id,
            "started_at": self.started_at,
            "steps": self.steps,
            "stats": {
                "total_tool_calls": self.total_tool_calls,
                "total_llm_calls": self.total_llm_calls,
                "total_ms": round(self.total_ms, 1),
            },
        }


class AgentLoop:
    """ReAct agent loop with 39 tools (19 ECMS + 20 CommandCode native)."""

    _MAX_ITERATIONS = 50

    def __init__(self, session_id: str, *, lightweight: bool = False,
                 model: str | None = None, api_key: str | None = None,
                 base_url: str | None = None,
                 progress_callback: Callable[[dict], None] | None = None,
                 agent_id: str | None = None,
                 event_queue: Any = None,
                 agent_profile: dict | None = None) -> None:
        settings = get_settings()
        self._session_id = session_id
        self._conv = Conversation(session_id)

        # Auto-append /v1 to base_url if not present
        resolved_base_url = base_url or settings.openai_base_url
        if resolved_base_url and not resolved_base_url.rstrip("/").endswith("/v1"):
            resolved_base_url = resolved_base_url.rstrip("/") + "/v1"

        self._client = AsyncOpenAI(
            api_key=api_key or settings.openai_api_key,
            base_url=resolved_base_url,
        )
        self._model = model or settings.llm_model
        self._lightweight = lightweight
        self._progress_callback = progress_callback
        self._event_queue = event_queue
        self._agent_id = agent_id or session_id

        # Load agent profile synchronously if provided
        if agent_profile:
            self._custom_prompt = agent_profile.get("system_prompt_addon", "")
            import json as _json
            tp = agent_profile.get("tool_policy", "{}")
            self._tool_policy = _json.loads(tp) if isinstance(tp, str) else (tp or {})
            logger.info("[%s] Using agent profile: prompt_addon=%d chars",
                        session_id[:8], len(self._custom_prompt))
        self._trace = AgentTrace(
            session_id=session_id,
            trace_id=f"trace-{session_id[:8]}",
        )
        # Memory tiers
        self._working = WorkingMemory()
        self._session = SessionContext(session_id)
        set_agent_context(self._working, self._session)

        # CommandCode tool context — workspace-scoped
        self._cc_context = CCToolContext(
            cwd=Path("/workspace"),
            workspace_roots=[Path("/workspace"), Path("/app")],
        )
        set_cc_context(self._cc_context)

    def _load_agent_profile(self, agent_id: str) -> None:
        """Load agent configuration from the agents table."""
        try:
            from ecms.persistence.database.rest_session import db_session
            from sqlalchemy import text
            import asyncio as _asyncio

            async def _load():
                async with db_session() as s:
                    row = (await s.execute(
                        text("SELECT * FROM agents WHERE id = :aid"),
                        {"aid": agent_id},
                    )).first()
                    if not row:
                        return
                    d = {k.lower(): v for k, v in row._mapping.items() if v is not None}

                    # Apply system prompt addon
                    addon = d.get("system_prompt_addon", "")
                    if addon:
                        from ecms.memory.system_prompt import AGENTIC_SYSTEM_PROMPT
                        self._custom_prompt = addon
                        logger.info("[%s] Loaded agent profile: %s", agent_id, d.get("name", "unknown"))

                    # Apply tool policy
                    tool_policy_raw = d.get("tool_policy", "{}")
                    if isinstance(tool_policy_raw, str):
                        import json as _json
                        tool_policy_raw = _json.loads(tool_policy_raw)
                    self._tool_policy = tool_policy_raw

            # Run the async load in the main event loop
            try:
                loop = _asyncio.get_running_loop()
                loop.create_task(_load())
            except RuntimeError:
                _asyncio.run(_load())
        except Exception as e:
            logger.warning("[%s] Failed to load agent profile: %s", agent_id, e)

    async def run(self, prompt: str) -> tuple[str, dict]:
        """Process a user prompt. Returns (answer, trace_dict)."""
        t_start = time.perf_counter()
        self._trace.started_at = time.strftime("%H:%M:%S")
        self._trace.add_step("start", f"User: {prompt[:120]}")
        logger.info("[%s] START agent turn | prompt=%.100s", self._trace.trace_id, prompt)

        # Track in working memory
        self._conv.add("user", prompt)
        self._working.scratchpad = ""

        while True:
            iteration = self._trace.total_llm_calls
            iter_start = time.perf_counter()
            messages = await self._build_messages()
            effective_tools = self._build_tools()
            try:
                response = await self._client.chat.completions.create(
                    model=self._model,
                    messages=messages,
                    tools=effective_tools,
                    tool_choice="auto",
                    temperature=0.2,
                    max_tokens=4000,
                )
                llm_ms = (time.perf_counter() - iter_start) * 1000
                logger.info(
                    "[%s] LLM call #%d | %.0fms | tokens=%s",
                    self._trace.trace_id, iteration + 1, llm_ms,
                    response.usage.total_tokens if response.usage else "?",
                )
            except Exception as e:
                llm_ms = (time.perf_counter() - iter_start) * 1000
                logger.warning("[%s] LLM call #%d FAILED (%.0fms): %s",
                               self._trace.trace_id, iteration + 1, llm_ms, e)
                self._trace.add_step("error", f"LLM call #{iteration+1} failed: {e}", llm_ms)
                last = self._conv.last_message
                if last and last["role"] == "assistant" and last.get("content"):
                    return last["content"], self._trace.to_dict()
                if iteration == 0:
                    return f"LLM connection failed: {e}", self._trace.to_dict()
                return "I was unable to complete my reasoning.", self._trace.to_dict()

            choice = response.choices[0]
            msg = choice.message

            # Agent decided to respond (no more tools)
            if not msg.tool_calls:
                content = msg.content or ""
                self._conv.add("assistant", content)
                total_ms = (time.perf_counter() - t_start) * 1000
                self._trace.total_ms = total_ms
                self._trace.add_step(
                    "respond", f"Answered in {len(content)} chars", total_ms,
                    data={"iterations": iteration + 1, "answer_preview": content[:200]},
                )
                logger.info(
                    "[%s] DONE | %d iterations | %.0fms | %.100s",
                    self._trace.trace_id, iteration + 1, total_ms, content,
                )
                return content, self._trace.to_dict()

            # Max iterations reached — make one final wrap-up call
            if iteration >= self._MAX_ITERATIONS:
                self._trace.add_step("wrapup", f"Max iterations ({self._MAX_ITERATIONS}) reached", 0)
                logger.info("[%s] WRAPUP at max iterations=%d", self._trace.trace_id, iteration + 1)

                try:
                    # Gather all findings from the conversation
                    conv_summary = self._conv.get_summary() if hasattr(self._conv, 'get_summary') else str(self._conv.messages[-10:])

                    wrap_prompt = (
                        "You have reached your reasoning iteration limit. "
                        "Synthesize everything you have learned so far from the tool results into a comprehensive, well-structured answer. "
                        "Do NOT mention the limit or that you were stopped. Just compile what you know. "
                        f"Findings so far:\n{conv_summary}"
                    )

                    wrap_messages = [
                        {"role": "system", "content": "You are an AI coding assistant. Synthesize findings into a concise, helpful answer."},
                        {"role": "user", "content": wrap_prompt},
                    ]

                    wrap_response = await self._client.chat.completions.create(
                        model=self._model,
                        messages=wrap_messages,
                        temperature=0.2,
                        max_tokens=2000,
                    )
                    content = wrap_response.choices[0].message.content or "I was unable to complete my reasoning."
                except Exception as wrap_err:
                    logger.warning("[%s] Wrap-up call failed: %s", self._trace.trace_id, wrap_err)
                    content = "I was unable to complete my reasoning."

                self._conv.add("assistant", content)
                total_ms = (time.perf_counter() - t_start) * 1000
                self._trace.total_ms = total_ms
                return content, self._trace.to_dict()

            # Agent wants tools → log each
            tool_names = [tc.function.name for tc in msg.tool_calls]
            preview = msg.content[:100] if msg.content else f"calling {', '.join(tool_names)}"
            self._trace.add_step(
                "thinking", preview, llm_ms,
                data={"iteration": iteration + 1, "tool_calls": tool_names},
            )
            logger.info(
                "[%s] THINK iteration=%d | tools=%s | %.100s",
                self._trace.trace_id, iteration + 1, tool_names, preview,
            )

            self._conv.add("assistant", content=msg.content,
                           tool_calls=[
                               {"id": tc.id, "type": "function",
                                "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                               for tc in msg.tool_calls
                           ])

            for tc in msg.tool_calls:
                tc_start = time.perf_counter()
                name = tc.function.name
                try:
                    args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    args = {}
                logger.info("[%s] EXEC %s(%s)", self._trace.trace_id, name, args)

                # Notify orchestrator of progress
                if self._progress_callback:
                    try:
                        self._progress_callback({
                            "type": "task_progress",
                            "iteration": iteration + 1,
                            "tool_name": name,
                            "agent_id": agent_id or self._session_id,
                        })
                    except Exception:
                        pass

                try:
                    result = await invoke_tool(name, args)
                except Exception as tool_exc:  # noqa: BLE001
                    result = f"Tool '{name}' failed: {tool_exc}"
                    logger.warning("[%s] TOOL %s FAILED: %s", self._trace.trace_id, name, tool_exc)
                tc_ms = (time.perf_counter() - tc_start) * 1000

                # Capture tool result as knowledge — fire-and-forget
                capture_tool_result(name, args, result, session_id=self._session_id)

                # Sync plan mode between ECMS and CC context
                if name == "enter_plan_mode":
                    self._working.plan_mode = True
                    self._cc_context.plan_mode = True
                elif name == "exit_plan_mode":
                    self._working.plan_mode = False
                    self._cc_context.plan_mode = False

                self._trace.add_step(
                    "tool_call", f"{name}({', '.join(f'{k}={v}' for k,v in args.items())})",
                    tc_ms,
                    data={"tool": name, "args": args, "result_len": len(result), "result_preview": result[:200]},
                )
                logger.info(
                    "[%s] RESULT %s | %.0fms | %d chars | %.150s",
                    self._trace.trace_id, name, tc_ms, len(result), result,
                )
                self._conv.add("tool", result, tool_call_id=tc.id, name=name)

    def _build_tools(self) -> list[dict]:
        """Return the tool list filtered by current plan mode."""
        return get_effective_tools(plan_mode=self._working.plan_mode)

    async def _build_messages(self) -> list[dict]:
        """Build messages with production context blocks injected."""
        context_blocks: list[str] = []

        if not self._lightweight:
            # <context_environment> — live system data (always present)
            context_blocks.append(
                _build_environment_block(self._session_id, self._working.plan_mode)
            )

            # <context_skills> — bundled skills from disk (always present)
            context_blocks.append(_build_skills_block())

            # <context_tools> — tool names + schemas (always present)
            context_blocks.append(_build_tools_block(self._build_tools()))

            # <context_memory> — working memory + session context (agent-controlled)
            wm_summary = self._working.summary_for_agent()
            sm_snap = await self._session.snapshot()
            sm_summary = ""
            if sm_snap:
                lines = ["## Session Context (remembered from earlier in this conversation)"]
                for k, v in sorted(sm_snap.items()):
                    lines.append(f"- **{k}**: {str(v)[:200]}")
                sm_summary = "\n".join(lines)
            memory_parts = []
            if wm_summary:
                memory_parts.append(wm_summary)
            if sm_summary:
                memory_parts.append(sm_summary)
            if memory_parts:
                context_blocks.append(
                    "<context_memory>\n" + "\n".join(memory_parts) + "\n</context_memory>"
                )

            # <context_knowledge_graph> — tool discoveries this turn (agent-controlled)
            kg_parts = []
            if self._working.active_atom_ids:
                kg_parts.append(f"Active memory atoms: {', '.join(self._working.active_atom_ids[:10])}")
            if self._working.active_graph_refs:
                kg_parts.append(f"Active graph references: {', '.join(self._working.active_graph_refs[:10])}")
            if kg_parts:
                context_blocks.append(
                    "<context_knowledge_graph>\n" + "\n".join(kg_parts) + "\n</context_knowledge_graph>"
                )

        # Assemble
        context_block_text = "\n\n".join(context_blocks)
        if self._lightweight:
            system_content = context_block_text or "You are a helpful coding agent."
        elif hasattr(self, '_custom_prompt') and self._custom_prompt:
            prefix = context_block_text + "\n\n" if context_block_text else ""
            system_content = prefix + self._custom_prompt
        else:
            prefix = context_block_text + "\n\n" if context_block_text else ""
            system_content = prefix + AGENTIC_SYSTEM_PROMPT

        system = {"role": "system", "content": system_content}
        history = self._conv.as_list()
        return [system] + history

    @property
    def conversation(self) -> Conversation:
        return self._conv

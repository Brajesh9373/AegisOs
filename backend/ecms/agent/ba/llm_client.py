"""Resilient BA LLM client — timeout, retry, circuit breaker, fallback.

Wraps AsyncOpenAI so every BA stage gets the same production behavior:
- per-attempt timeout via asyncio.wait_for
- retriable errors: 429 / 500 / 502 / 503 / 504 / timeout / connection
- exponential backoff with jitter
- circuit breaker per (model, base_url)
- fallback model support
- structured LlmProviderError on final failure (never raw openai.*Error)

The client is intentionally thin — no prompt logic here, just infrastructure.
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
import time
from dataclasses import dataclass
from typing import Any

from ecms.shared.exceptions import LlmProviderError

logger = logging.getLogger("ecms.ba.llm_client")

__all__ = ["BaLlmClient", "LlmCallOpts", "get_ba_llm_client"]


FINALIZE_OPTS = None  # set lazily to avoid dataclass ordering issues
DEFAULT_OPTS = None


@dataclass
class LlmCallOpts:
    timeout_s: float = 90.0
    max_retries: int = 2
    backoff_base: float = 1.5
    jitter: float = 0.2
    breaker_threshold: int = 5
    breaker_window_s: float = 60.0
    breaker_open_s: float = 30.0

    @classmethod
    def for_finalize(cls) -> LlmCallOpts:
        """180s per attempt for the 6k-token finalize emit — user's approved budget."""
        return cls(
            timeout_s=180.0,
            max_retries=1,
            backoff_base=1.5,
            jitter=0.2,
            breaker_threshold=5,
            breaker_window_s=60.0,
            breaker_open_s=30.0,
        )


_breaker: dict[tuple[str, str], dict[str, Any]] = {}


def _breaker_key(model: str, base_url: str | None) -> tuple[str, str]:
    return (model or "", base_url or "")


def _is_circuit_open(model: str, base_url: str | None) -> bool:
    key = _breaker_key(model, base_url or "")
    state = _breaker.get(key)
    if not state:
        return False
    open_until = state.get("open_until")
    if open_until and time.monotonic() < open_until:
        return True
    if open_until and time.monotonic() >= open_until:
        state["open_until"] = None
        state["failures"] = 0
    return False


def _record_success(model: str, base_url: str | None) -> None:
    key = _breaker_key(model, base_url or "")
    state = _breaker.get(key)
    if state:
        state["failures"] = 0
        state["open_until"] = None


def _record_failure(model: str, base_url: str | None, opts: LlmCallOpts | None = None) -> None:
    o = opts or LlmCallOpts()
    key = _breaker_key(model, base_url or "")
    state = _breaker.setdefault(
        key, {"failures": 0, "window_start": time.monotonic(), "open_until": None}
    )
    now = time.monotonic()
    if now - state["window_start"] > o.breaker_window_s:
        state["failures"] = 0
        state["window_start"] = now
        state["open_until"] = None
    state["failures"] += 1
    if state["failures"] >= o.breaker_threshold:
        state["open_until"] = now + o.breaker_open_s
        logger.warning(
            "[ba.llm_client] circuit_open model=%s failures=%d open_for=%ds",
            model,
            state["failures"],
            int(o.breaker_open_s),
        )


def _is_retriable(exc: BaseException) -> bool:
    name = type(exc).__name__
    if name in ("RateLimitError", "APITimeoutError", "APIConnectionError", "InternalServerError"):
        return True
    if name in ("APITimeoutError", "TimeoutError") or isinstance(exc, asyncio.TimeoutError):
        return True
    status = getattr(exc, "status_code", None)
    if status in (429, 500, 502, 503, 504):
        return True
    msg = str(exc).lower()
    if "timeout" in msg or "connection" in msg or "rate limit" in msg:
        return True
    return False


def _to_llm_provider_error(exc: BaseException, model: str) -> LlmProviderError:
    status = getattr(exc, "status_code", None)
    code = "llm_rate_limited" if status == 429 else "llm_provider_error"
    details: dict[str, Any] = {"model": model, "error_type": type(exc).__name__}
    if status is not None:
        details["status_code"] = status
    retry_after = (
        getattr(exc, "headers", {}).get("retry-after") if hasattr(exc, "headers") else None
    )
    if retry_after:
        details["retry_after"] = retry_after
    return LlmProviderError(str(exc) or type(exc).__name__, code=code, details=details)


def _backoff(attempt: int, opts: LlmCallOpts) -> float:
    base = opts.backoff_base**attempt
    jitter = random.uniform(0, opts.jitter * base)
    return base + jitter


class BaLlmClient:
    """Resilient wrapper around AsyncOpenAI for BA stages."""

    def __init__(
        self, model: str, api_key: str, base_url: str | None, opts: LlmCallOpts | None = None
    ) -> None:
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.opts = opts or LlmCallOpts()
        self._openai_client = None

    def _convert_tools_to_anthropic(
        self, tools: list[dict[str, Any]] | None
    ) -> list[dict[str, Any]] | None:
        """Convert OpenAI-style tools to Anthropic format.

        OpenAI: {"type": "function", "function": {"name": "...", "parameters": {...}}}
        Anthropic: {"name": "...", "input_schema": {...}}
        """
        if not tools:
            return None

        anthropic_tools = []
        for tool in tools:
            if tool.get("type") == "function":
                func = tool.get("function", {})
                anthropic_tool = {
                    "name": func.get("name"),
                    "description": func.get("description", ""),
                    "input_schema": func.get("parameters", {"type": "object", "properties": {}}),
                }
                anthropic_tools.append(anthropic_tool)
            else:
                # Already in Anthropic format or unknown - pass through
                anthropic_tools.append(tool)

        return anthropic_tools

    def _normalize_response(self, anthropic_resp: Any) -> Any:
        """Normalize Anthropic response to OpenAI format for backward compatibility."""
        from types import SimpleNamespace

        # Extract text content from Anthropic response
        text_content = ""
        if hasattr(anthropic_resp, "content") and anthropic_resp.content:
            for block in anthropic_resp.content:
                if hasattr(block, "type") and block.type == "text":
                    text_content += getattr(block, "text", "")

        # Extract tool calls if present
        tool_calls = []
        if hasattr(anthropic_resp, "content"):
            for block in anthropic_resp.content:
                if hasattr(block, "type") and block.type == "tool_use":
                    tool_calls.append(
                        SimpleNamespace(
                            id=getattr(block, "id", ""),
                            type="function",
                            function=SimpleNamespace(
                                name=getattr(block, "name", ""),
                                arguments=json.dumps(getattr(block, "input", {})),
                            ),
                        )
                    )

        # Create OpenAI-style response object
        message = SimpleNamespace(
            role="assistant", content=text_content, tool_calls=tool_calls if tool_calls else None
        )

        choice = SimpleNamespace(
            index=0, message=message, finish_reason=getattr(anthropic_resp, "stop_reason", "stop")
        )

        response = SimpleNamespace(
            id=getattr(anthropic_resp, "id", ""),
            object="chat.completion",
            created=int(time.time()),
            model=getattr(anthropic_resp, "model", self.model),
            choices=[choice],
            usage=SimpleNamespace(
                prompt_tokens=getattr(getattr(anthropic_resp, "usage", None), "input_tokens", 0),
                completion_tokens=getattr(
                    getattr(anthropic_resp, "usage", None), "output_tokens", 0
                ),
                total_tokens=getattr(getattr(anthropic_resp, "usage", None), "input_tokens", 0)
                + getattr(getattr(anthropic_resp, "usage", None), "output_tokens", 0),
            ),
        )

        return response

    def _get_openai_client(self):
        if self._openai_client is None:
            # Use Anthropic SDK for GLM-5 custom endpoint
            from anthropic import AsyncAnthropic

            self._openai_client = AsyncAnthropic(
                api_key=self.api_key,
                base_url=self.base_url,
                default_headers={
                    "X-Claude-Code-Session-Id": "ba-agent-session",
                    "Authorization": f"Bearer {self.api_key}",
                },
            )
        return self._openai_client

    async def chat(
        self,
        *,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        tool_choice: dict[str, Any] | None = None,
        temperature: float = 0.0,
        max_tokens: int | None = None,
    ) -> Any:
        if _is_circuit_open(self.model, self.base_url):
            raise LlmProviderError(
                f"LLM circuit open for {self.model}",
                code="llm_circuit_open",
                details={"model": self.model, "error_type": "CircuitOpen"},
            )

        client = self._get_openai_client()
        last_exc: BaseException | None = None

        for attempt in range(self.opts.max_retries + 1):
            try:
                t0 = time.perf_counter()

                # Convert OpenAI-style messages to Anthropic format
                anthropic_messages = []
                system_prompt = None
                for msg in messages:
                    if msg.get("role") == "system":
                        system_prompt = msg.get("content")
                    else:
                        anthropic_messages.append(msg)

                kwargs: dict[str, Any] = {
                    "model": self.model,
                    "messages": anthropic_messages,
                    "max_tokens": max_tokens or 4096,
                }
                if system_prompt:
                    kwargs["system"] = system_prompt
                if tools is not None:
                    # Convert OpenAI tool format to Anthropic format
                    kwargs["tools"] = self._convert_tools_to_anthropic(tools)
                if temperature != 0.0:
                    kwargs["temperature"] = temperature

                resp = await asyncio.wait_for(
                    client.messages.create(**kwargs),
                    timeout=self.opts.timeout_s,
                )
                _record_success(self.model, self.base_url)
                elapsed = int((time.perf_counter() - t0) * 1000)
                logger.info(
                    "[ba.llm_client] success model=%s latency_ms=%d attempt=%d",
                    self.model,
                    elapsed,
                    attempt,
                )

                # Normalize Anthropic response to OpenAI format for compatibility
                return self._normalize_response(resp)

            except TimeoutError as exc:
                last_exc = exc
                _record_failure(self.model, self.base_url, self.opts)
                if attempt >= self.opts.max_retries:
                    break
                delay = _backoff(attempt, self.opts)
                logger.warning(
                    "[ba.llm_client] timeout model=%s attempt=%d/%d retry_in=%.1fs",
                    self.model,
                    attempt,
                    self.opts.max_retries,
                    delay,
                )
                await asyncio.sleep(delay)
                continue

            except Exception as exc:
                last_exc = exc
                retriable = _is_retriable(exc)
                _record_failure(self.model, self.base_url, self.opts)
                if not retriable or attempt >= self.opts.max_retries:
                    elapsed = getattr(exc, "status_code", None)
                    logger.warning(
                        "[ba.llm_client] failed model=%s error=%s status=%s retriable=%s attempt=%d",
                        self.model,
                        type(exc).__name__,
                        elapsed,
                        retriable,
                        attempt,
                    )
                    raise _to_llm_provider_error(exc, self.model) from exc
                delay = _backoff(attempt, self.opts)
                logger.warning(
                    "[ba.llm_client] retriable model=%s error=%s attempt=%d/%d retry_in=%.1fs",
                    self.model,
                    type(exc).__name__,
                    attempt,
                    self.opts.max_retries,
                    delay,
                )
                await asyncio.sleep(delay)
                continue

        if last_exc is not None:
            if isinstance(last_exc, asyncio.TimeoutError):
                raise LlmProviderError(
                    f"LLM timeout after {self.opts.max_retries + 1} attempts",
                    code="llm_timeout",
                    details={"model": self.model, "error_type": "TimeoutError"},
                ) from last_exc
            raise _to_llm_provider_error(last_exc, self.model) from last_exc
        raise LlmProviderError("LLM call failed", details={"model": self.model})


async def get_ba_llm_client(opts: LlmCallOpts | None = None) -> BaLlmClient:
    """Resolve BA model config and return a resilient client."""
    from ecms.agent.ba.model import resolve_ba_model

    cfg = await resolve_ba_model()
    model = cfg.get("model") or ""
    api_key = cfg.get("api_key") or ""
    base_url = cfg.get("base_url") or None
    if not model or not api_key:
        raise LlmProviderError(
            "BA model not configured", code="ba_model_not_configured", details={"model": model}
        )
    return BaLlmClient(model=model, api_key=api_key, base_url=base_url, opts=opts)

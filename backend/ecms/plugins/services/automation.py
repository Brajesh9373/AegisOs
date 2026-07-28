"""Automation engine (SECTION 272).

Automations trigger from events. Rules map an event type to an async handler; when
a matching event is published (or triggered manually), every matching handler
runs. Automations execute through the Runtime, never bypassing it.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from ecms.events import EventBus
from ecms.shared.events import BaseEvent

__all__ = ["AutomationEngine", "AutomationRule"]

AutomationHandler = Callable[[BaseEvent], Awaitable[None]]


@dataclass(slots=True)
class AutomationRule:
    """A rule binding an event type to a handler (SECTION 272)."""

    event_type: str
    handler: AutomationHandler


class AutomationEngine:
    """Triggers automations from events (SECTION 272)."""

    def __init__(self, *, event_bus: EventBus | None = None) -> None:
        """Initialize the engine, subscribing to the event bus when provided."""
        self._rules: list[AutomationRule] = []
        self._fired = 0
        if event_bus is not None:
            event_bus.subscribe(self._dispatch)

    def on(self, event_type: str, handler: AutomationHandler) -> None:
        """Register an automation rule for an event type."""
        self._rules.append(AutomationRule(event_type=event_type, handler=handler))

    async def trigger(self, event: BaseEvent) -> None:
        """Dispatch an event to matching automation rules manually."""
        await self._dispatch(event)

    @property
    def fired(self) -> int:
        """Return the number of times automation handlers have fired."""
        return self._fired

    async def _dispatch(self, event: BaseEvent) -> None:
        for rule in self._rules:
            if rule.event_type == event.event_type:
                self._fired += 1
                await rule.handler(event)

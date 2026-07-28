"""Goal engine (SECTION 284).

Decomposes a user prompt into one or more goals. A goal's definition is immutable
during execution; the planner sequences them into an execution plan.
"""

from __future__ import annotations

import re

from ecms.shared.models import Goal

__all__ = ["GoalEngine"]

_SPLIT = re.compile(r"\b(?:and then|then)\b|;|\band\b", re.IGNORECASE)


class GoalEngine:
    """Converts a prompt into a goal tree (SECTION 284)."""

    def decompose(self, prompt: str) -> list[Goal]:
        """Split a prompt into a root goal and its sub-goals."""
        fragments = [fragment.strip() for fragment in _SPLIT.split(prompt) if fragment.strip()]
        if not fragments:
            fragments = [prompt.strip() or "achieve the request"]
        root = Goal(description=fragments[0])
        sub_goals = [
            Goal(description=fragment, parent_goal=root.goal_id) for fragment in fragments[1:]
        ]
        root.sub_goals = [goal.goal_id for goal in sub_goals]
        return [root, *sub_goals]

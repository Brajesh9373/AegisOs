"""Connector domain models (SECTION 121/122).

A connector *discovers* objects in an external system and *normalizes* them into
Universal Knowledge Objects. It never reasons or writes knowledge.
"""

from __future__ import annotations

from typing import Any

from pydantic import Field

from ecms.shared.models.base import DomainModel

__all__ = ["DiscoveredObject", "SyncResult"]


class DiscoveredObject(DomainModel):
    """A raw object discovered in an external system (SECTION 121)."""

    object_id: str
    object_type: str
    title: str
    content: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class SyncResult(DomainModel):
    """A summary of one synchronization run (SECTION 122)."""

    connector: str
    discovered: int = 0
    published: int = 0
    uko_ids: list[str] = Field(default_factory=list)

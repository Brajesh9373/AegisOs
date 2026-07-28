"""Plugin manifest and lifecycle state (SECTION 61/103)."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from ecms.shared.models.base import DomainModel

__all__ = ["PluginManifest", "PluginState"]


class PluginState(StrEnum):
    """Lifecycle state of a registered plugin."""

    REGISTERED = "registered"
    INITIALIZED = "initialized"
    STARTED = "started"
    STOPPED = "stopped"
    FAILED = "failed"


class PluginManifest(DomainModel):
    """Metadata every plugin declares (SECTION 61)."""

    name: str
    version: str
    capabilities: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    produced_events: list[str] = Field(default_factory=list)
    consumed_events: list[str] = Field(default_factory=list)

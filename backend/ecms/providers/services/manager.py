"""Connector manager: the single entry point for integrations (SECTION 118).

Owns registered connectors and runs synchronization: discover, normalize into
UKOs, and publish. Full sync processes everything; incremental sync processes only
objects whose checksum changed. Every stage emits an event.
"""

from __future__ import annotations

from ecms.events import EventBus
from ecms.providers.events.connector_events import (
    connector_registered,
    discovery_completed,
    discovery_started,
    sync_completed,
    sync_started,
    uko_published,
)
from ecms.providers.infrastructure.change_detection import ChangeDetector
from ecms.providers.interfaces.connector import Connector
from ecms.providers.services.registry import ConnectorRegistry
from ecms.shared.events import BaseEvent
from ecms.shared.models import UniversalKnowledgeObject

__all__ = ["ConnectorManager"]


class ConnectorManager:
    """The single entry point for all enterprise integrations (SECTION 118)."""

    def __init__(
        self,
        *,
        registry: ConnectorRegistry | None = None,
        change_detector: ChangeDetector | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize with a registry, change detector and optional event bus."""
        self._registry = registry or ConnectorRegistry()
        self._change = change_detector or ChangeDetector()
        self._event_bus = event_bus

    @property
    def registry(self) -> ConnectorRegistry:
        """Return the connector registry."""
        return self._registry

    async def register(self, connector: Connector) -> None:
        """Register a connector and announce it."""
        self._registry.register(connector)
        await self._emit(connector_registered(connector.name))

    async def full_sync(
        self, connector_name: str, *, organization_id: str
    ) -> list[UniversalKnowledgeObject]:
        """Discover and publish every object as a UKO (SECTION 122)."""
        connector = self._registry.get(connector_name)
        await self._emit(sync_started(connector_name))
        await self._emit(discovery_started(connector_name))
        discovered = await connector.discover()
        await self._emit(discovery_completed(connector_name, len(discovered)))
        ukos: list[UniversalKnowledgeObject] = []
        for obj in discovered:
            uko = connector.normalize(obj, organization_id=organization_id)
            self._change.has_changed(obj.object_id, uko.checksum or "")
            ukos.append(uko)
            await self._emit(uko_published(uko.uko_id))
        await self._emit(sync_completed(connector_name, len(ukos)))
        return ukos

    async def incremental_sync(
        self, connector_name: str, *, organization_id: str
    ) -> list[UniversalKnowledgeObject]:
        """Publish only objects whose checksum changed since last sync (SECTION 123)."""
        connector = self._registry.get(connector_name)
        await self._emit(sync_started(connector_name))
        discovered = await connector.discover()
        changed: list[UniversalKnowledgeObject] = []
        for obj in discovered:
            uko = connector.normalize(obj, organization_id=organization_id)
            if self._change.has_changed(obj.object_id, uko.checksum or ""):
                changed.append(uko)
                await self._emit(uko_published(uko.uko_id))
        await self._emit(sync_completed(connector_name, len(changed)))
        return changed

    async def _emit(self, event: BaseEvent) -> None:
        if self._event_bus is not None:
            await self._event_bus.publish(event)

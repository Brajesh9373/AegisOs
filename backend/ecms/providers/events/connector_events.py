"""Connector event factories (SECTION 129).

Every stage of the connector pipeline publishes an event in the PROVIDER category
so synchronization is observable and auditable.
"""

from __future__ import annotations

from typing import Any

from ecms.shared.enums import EventCategory
from ecms.shared.events import BaseEvent, make_event

__all__ = [
    "connector_registered",
    "discovery_completed",
    "discovery_started",
    "sync_completed",
    "sync_started",
    "uko_published",
]

_PRODUCER = "connector-runtime"


def _event(event_type: str, payload: dict[str, Any]) -> BaseEvent:
    return make_event(event_type, EventCategory.PROVIDER, _PRODUCER, payload=payload)


def connector_registered(connector: str) -> BaseEvent:
    """Emitted when a connector is registered (SECTION 129)."""
    return _event("ConnectorRegistered", {"connector": connector})


def sync_started(connector: str) -> BaseEvent:
    """Emitted when synchronization starts (SECTION 129)."""
    return _event("SyncStarted", {"connector": connector})


def sync_completed(connector: str, published: int) -> BaseEvent:
    """Emitted when synchronization completes (SECTION 129)."""
    return _event("SyncCompleted", {"connector": connector, "published": published})


def discovery_started(connector: str) -> BaseEvent:
    """Emitted when discovery starts (SECTION 129)."""
    return _event("DiscoveryStarted", {"connector": connector})


def discovery_completed(connector: str, discovered: int) -> BaseEvent:
    """Emitted when discovery completes (SECTION 129)."""
    return _event("DiscoveryCompleted", {"connector": connector, "discovered": discovered})


def uko_published(uko_id: str) -> BaseEvent:
    """Emitted when a connector publishes a Universal Knowledge Object (SECTION 129)."""
    return _event("UkoPublished", {"uko_id": uko_id})

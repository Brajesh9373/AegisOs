"""Connector port (SECTION 85/117).

Every enterprise connector implements the same interface and produces Universal
Knowledge Objects. Connectors only observe; they never modify knowledge, activate
memory, reason or execute tools.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ecms.providers.domain.connector import DiscoveredObject
from ecms.shared.models import UniversalKnowledgeObject

__all__ = ["Connector"]


@runtime_checkable
class Connector(Protocol):
    """An enterprise connector that observes an external system (SECTION 117).

    Operations:
        name: The connector's stable identifier.
        provider: The external platform this connector observes.
        initialize: Prepare the connector for use.
        authenticate: Establish credentials with the external system.
        health: Report whether the connector is healthy.
        discover: Enumerate the objects available in the external system.
        collect: Fetch a single object by id.
        normalize: Convert a discovered object into a Universal Knowledge Object.
        shutdown: Release the connector's resources.
    """

    @property
    def name(self) -> str: ...
    @property
    def provider(self) -> str: ...
    async def initialize(self) -> None: ...
    async def authenticate(self) -> bool: ...
    async def health(self) -> bool: ...
    async def discover(self) -> list[DiscoveredObject]: ...
    async def collect(self, object_id: str) -> DiscoveredObject | None: ...
    def normalize(
        self, obj: DiscoveredObject, *, organization_id: str
    ) -> UniversalKnowledgeObject: ...
    async def shutdown(self) -> None: ...

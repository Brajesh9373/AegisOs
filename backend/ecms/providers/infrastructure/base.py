"""Base connector with default lifecycle and normalization (SECTION 114/124).

Concrete connectors implement :meth:`discover` and :meth:`collect`; the framework
provides authentication, health, and normalization to Universal Knowledge Objects
so connectors contain only provider-specific logic.
"""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod

from ecms.providers.domain.connector import DiscoveredObject
from ecms.shared.models import UniversalKnowledgeObject

__all__ = ["BaseConnector", "checksum"]


def checksum(content: str) -> str:
    """Return a stable SHA-256 checksum of content for change detection."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


class BaseConnector(ABC):
    """Abstract connector providing lifecycle and normalization defaults (SECTION 114)."""

    name: str = "connector"
    provider: str = "generic"

    async def initialize(self) -> None:
        """Prepare the connector for use (no-op by default)."""

    async def authenticate(self) -> bool:
        """Authenticate with the external system (succeeds by default)."""
        return True

    async def health(self) -> bool:
        """Report whether the connector is healthy (healthy by default)."""
        return True

    @abstractmethod
    async def discover(self) -> list[DiscoveredObject]:
        """Enumerate the objects available in the external system."""
        raise NotImplementedError

    @abstractmethod
    async def collect(self, object_id: str) -> DiscoveredObject | None:
        """Fetch a single object by id."""
        raise NotImplementedError

    def normalize(self, obj: DiscoveredObject, *, organization_id: str) -> UniversalKnowledgeObject:
        """Convert a discovered object into a Universal Knowledge Object (SECTION 124)."""
        return UniversalKnowledgeObject(
            provider=self.provider,
            provider_object_type=obj.object_type,
            provider_object_id=obj.object_id,
            organization_id=organization_id,
            title=obj.title,
            raw_content=obj.content,
            metadata=obj.metadata,
            checksum=checksum(obj.content),
        )

    async def shutdown(self) -> None:
        """Release the connector's resources (no-op by default)."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from legacy_ecms.core.uko import UniversalKnowledgeObject


class ProviderStatus(BaseModel):
    provider_name: str
    resource_id: str
    is_authenticated: bool
    last_sync_at: datetime | None = None
    objects_synced: int = 0
    errors: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class KnowledgeProvider(ABC):
    """Contract implemented by every enterprise connector."""

    provider_name: str
    provider_version: str

    @abstractmethod
    async def authenticate(self, credentials: dict[str, Any]) -> bool:
        """Authenticate with the external platform."""

    @abstractmethod
    async def discover(self) -> list[str]:
        """Discover available resource identifiers."""

    @abstractmethod
    async def sync(
        self,
        resource_id: str,
        since: datetime | None = None,
    ) -> AsyncIterator[UniversalKnowledgeObject]:
        """Yield UKOs discovered during full or incremental sync."""
        if False:
            yield  # pragma: no cover

    @abstractmethod
    async def validate(self) -> bool:
        """Return whether this provider is configured and reachable."""

    @abstractmethod
    async def get_status(self, resource_id: str) -> ProviderStatus:
        """Return sync and connectivity status for a resource."""

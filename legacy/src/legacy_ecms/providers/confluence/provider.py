from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any

from legacy_ecms.core.uko import UKOMetadata, UKOType, UniversalKnowledgeObject
from legacy_ecms.providers.base import KnowledgeProvider, ProviderStatus


class ConfluenceProvider(KnowledgeProvider):
    provider_name = "confluence"
    provider_version = "0.1.0"

    def __init__(self, pages: list[dict[str, Any]] | None = None) -> None:
        self.pages = pages or []
        self._authenticated = False

    async def authenticate(self, credentials: dict[str, Any]) -> bool:
        if "pages" in credentials:
            self.pages = list(credentials["pages"])
        self._authenticated = bool(self.pages) or bool(credentials.get("api_token"))
        return self._authenticated

    async def discover(self) -> list[str]:
        return sorted({page.get("space", "") for page in self.pages if page.get("space")})

    async def sync(self, resource_id: str, since: datetime | None = None) -> AsyncIterator[UniversalKnowledgeObject]:
        for page in self.pages:
            if resource_id != "*" and page.get("space") != resource_id:
                continue
            updated = self._parse_datetime(page.get("updated")) or datetime.now(UTC)
            if since and updated <= since:
                continue
            yield UniversalKnowledgeObject(
                id=f"confluence:page:{page.get('id')}",
                type=UKOType.DOCUMENT,
                name=page.get("title", page.get("id", "Confluence Page")),
                content=page.get("body", ""),
                metadata=UKOMetadata(
                    source=self.provider_name,
                    source_id=str(page.get("id")),
                    source_url=page.get("url"),
                    created_at=self._parse_datetime(page.get("created")) or updated,
                    modified_at=updated,
                    authors=[page["author"]] if page.get("author") else [],
                    tags=[page.get("space", "")],
                ),
                raw_data=page,
            )

    async def validate(self) -> bool:
        return self._authenticated or bool(self.pages)

    async def get_status(self, resource_id: str) -> ProviderStatus:
        return ProviderStatus(provider_name=self.provider_name, resource_id=resource_id, is_authenticated=self._authenticated)

    def _parse_datetime(self, value: Any) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=UTC)
        if isinstance(value, str):
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        return None

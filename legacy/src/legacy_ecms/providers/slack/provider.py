from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any

from legacy_ecms.core.uko import UKOMetadata, UKORelationship, UKOType, UniversalKnowledgeObject
from legacy_ecms.providers.base import KnowledgeProvider, ProviderStatus


class SlackProvider(KnowledgeProvider):
    provider_name = "slack"
    provider_version = "0.1.0"

    def __init__(self, messages: list[dict[str, Any]] | None = None) -> None:
        self.messages = messages or []
        self._authenticated = False

    async def authenticate(self, credentials: dict[str, Any]) -> bool:
        if "messages" in credentials:
            self.messages = list(credentials["messages"])
        self._authenticated = bool(self.messages) or bool(credentials.get("bot_token"))
        return self._authenticated

    async def discover(self) -> list[str]:
        return sorted({message.get("channel", "") for message in self.messages if message.get("channel")})

    async def sync(self, resource_id: str, since: datetime | None = None) -> AsyncIterator[UniversalKnowledgeObject]:
        for message in self.messages:
            if resource_id != "*" and message.get("channel") != resource_id:
                continue
            ts = self._parse_datetime(message.get("ts")) or datetime.now(UTC)
            if since and ts <= since:
                continue
            user = message.get("user")
            yield UniversalKnowledgeObject(
                id=f"slack:message:{message.get('channel')}:{message.get('ts')}",
                type=UKOType.MESSAGE,
                name=f"{message.get('channel')} message",
                content=message.get("text", ""),
                metadata=UKOMetadata(
                    source=self.provider_name,
                    source_id=f"{message.get('channel')}:{message.get('ts')}",
                    created_at=ts,
                    modified_at=ts,
                    authors=[user] if user else [],
                    tags=[message.get("channel", "")],
                ),
                relationships=[
                    UKORelationship(target_id=user, relationship="authored_by", target_type=UKOType.PERSON)
                ] if user else [],
                raw_data=message,
            )

    async def validate(self) -> bool:
        return self._authenticated or bool(self.messages)

    async def get_status(self, resource_id: str) -> ProviderStatus:
        return ProviderStatus(provider_name=self.provider_name, resource_id=resource_id, is_authenticated=self._authenticated)

    def _parse_datetime(self, value: Any) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=UTC)
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(float(value), tz=UTC)
        if isinstance(value, str):
            try:
                return datetime.fromtimestamp(float(value), tz=UTC)
            except ValueError:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
        return None

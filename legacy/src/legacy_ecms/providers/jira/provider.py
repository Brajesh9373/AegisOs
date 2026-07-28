from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any

from legacy_ecms.core.uko import UKOMetadata, UKORelationship, UKOType, UniversalKnowledgeObject
from legacy_ecms.providers.base import KnowledgeProvider, ProviderStatus


class JiraProvider(KnowledgeProvider):
    """Jira issue provider.

    The initial implementation accepts already-fetched issue dictionaries. A
    REST-backed collector can populate the same issue list without changing the
    provider contract or downstream pipeline.
    """

    provider_name = "jira"
    provider_version = "0.1.0"

    def __init__(self, issues: list[dict[str, Any]] | None = None) -> None:
        self.issues = issues or []
        self._authenticated = False
        self._last_sync_at: dict[str, datetime] = {}
        self._sync_counts: dict[str, int] = {}

    async def authenticate(self, credentials: dict[str, Any]) -> bool:
        supplied_issues = credentials.get("issues")
        if supplied_issues is not None:
            self.issues = list(supplied_issues)
        self._authenticated = bool(self.issues) or all(
            credentials.get(key) for key in ("base_url", "email", "api_token")
        )
        return self._authenticated

    async def discover(self) -> list[str]:
        projects = {issue.get("key", "").split("-", 1)[0] for issue in self.issues if issue.get("key")}
        return sorted(project for project in projects if project)

    async def sync(
        self,
        resource_id: str,
        since: datetime | None = None,
    ) -> AsyncIterator[UniversalKnowledgeObject]:
        count = 0
        for issue in self.issues:
            key = issue.get("key", "")
            if resource_id != "*" and not key.startswith(f"{resource_id}-"):
                continue
            updated = self._parse_datetime(issue.get("updated")) or datetime.now(UTC)
            if since is not None and updated <= since:
                continue
            count += 1
            yield self._issue_to_uko(issue, updated)
        self._last_sync_at[resource_id] = datetime.now(UTC)
        self._sync_counts[resource_id] = count

    async def validate(self) -> bool:
        return self._authenticated or bool(self.issues)

    async def get_status(self, resource_id: str) -> ProviderStatus:
        return ProviderStatus(
            provider_name=self.provider_name,
            resource_id=resource_id,
            is_authenticated=self._authenticated,
            last_sync_at=self._last_sync_at.get(resource_id),
            objects_synced=self._sync_counts.get(resource_id, 0),
        )

    def _issue_to_uko(self, issue: dict[str, Any], updated: datetime) -> UniversalKnowledgeObject:
        key = issue["key"]
        created = self._parse_datetime(issue.get("created")) or updated
        assignee = self._person_name(issue.get("assignee"))
        reporter = self._person_name(issue.get("reporter"))
        labels = list(issue.get("labels", []))
        status = issue.get("status")
        content_parts = [
            issue.get("summary", ""),
            issue.get("description", ""),
            *(comment.get("body", "") for comment in issue.get("comments", [])),
        ]
        events = []
        for change in issue.get("changelog", []):
            events.append(
                {
                    "name": f"Jira {key} {change.get('field', 'field')} changed",
                    "actor": self._person_name(change.get("author")),
                    "occurred_at": change.get("created", updated.isoformat()),
                    "from": change.get("from"),
                    "to": change.get("to"),
                }
            )

        relationships: list[UKORelationship] = []
        if assignee:
            relationships.append(
                UKORelationship(
                    target_id=assignee,
                    relationship="assigned_to",
                    target_type=UKOType.PERSON,
                )
            )
        if reporter:
            relationships.append(
                UKORelationship(
                    target_id=reporter,
                    relationship="reported_by",
                    target_type=UKOType.PERSON,
                )
            )

        return UniversalKnowledgeObject(
            id=f"jira:ticket:{key}",
            type=UKOType.TICKET,
            name=f"{key}: {issue.get('summary', key)}",
            content="\n\n".join(part for part in content_parts if part),
            metadata=UKOMetadata(
                source=self.provider_name,
                source_id=key,
                source_url=issue.get("url"),
                created_at=created,
                modified_at=updated,
                authors=[person for person in [reporter, assignee] if person],
                tags=[tag for tag in [status, *labels] if tag],
            ),
            relationships=relationships,
            raw_data={**issue, "events": events},
        )

    def _person_name(self, person: Any) -> str | None:
        if person is None:
            return None
        if isinstance(person, str):
            return person
        return person.get("displayName") or person.get("name") or person.get("emailAddress")

    def _parse_datetime(self, value: Any) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=UTC)
        if isinstance(value, str):
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        return None

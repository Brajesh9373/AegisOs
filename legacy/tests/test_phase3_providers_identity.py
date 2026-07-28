from datetime import UTC, datetime

import pytest

from ecms.core.uko import UKOMetadata, UKORelationship, UKOType, UniversalKnowledgeObject
from ecms.pipeline.identity import IdentityResolver
from ecms.pipeline.orchestrator import PipelineOrchestrator
from ecms.pipeline.structural.sql_parser import SqlStructuralExtractor
from ecms.providers.confluence import ConfluenceProvider
from ecms.providers.mysql import MySQLProvider
from ecms.providers.slack import SlackProvider


def test_sql_structural_extractor_finds_tables_columns_and_foreign_keys() -> None:
    ddl = """
    CREATE TABLE orders (
      id UUID PRIMARY KEY,
      customer_id UUID,
      FOREIGN KEY (customer_id) REFERENCES customers(id)
    );
    """

    result = SqlStructuralExtractor().extract(ddl)

    assert {artifact.name for artifact in result.artifacts} >= {"orders", "orders.id", "orders.customer_id"}
    assert result.relationships[0].relationship == "references"
    assert result.relationships[0].target_name == "customers"


@pytest.mark.asyncio
async def test_mysql_provider_syncs_table_schema_and_pipeline_derives_columns() -> None:
    provider = MySQLProvider(
        [
            {
                "name": "billing",
                "tables": [
                    {
                        "name": "orders",
                        "columns": [
                            {"name": "id", "type": "UUID"},
                            {"name": "customer_id", "type": "UUID"},
                        ],
                        "foreign_keys": [
                            {
                                "column": "customer_id",
                                "references_table": "customers",
                                "references_column": "id",
                            }
                        ],
                        "updated_at": "2026-07-01T00:00:00+00:00",
                    }
                ],
            }
        ]
    )

    assert await provider.discover() == ["billing"]
    ukos = [uko async for uko in provider.sync("billing")]
    episodes, _ = await PipelineOrchestrator().process_uko(ukos[0])

    assert ukos[0].type == UKOType.TABLE
    assert any(episode.uko.type == UKOType.COLUMN for episode in episodes)


@pytest.mark.asyncio
async def test_slack_and_confluence_providers_emit_standard_ukos() -> None:
    slack = SlackProvider(
        [{"channel": "eng", "ts": "1780000000.0", "user": "@brajesh", "text": "JWT auth rollout is live"}]
    )
    confluence = ConfluenceProvider(
        [
            {
                "id": "page-1",
                "space": "ENG",
                "title": "Authentication Design",
                "body": "# Authentication\nJWT rollout notes",
                "updated": "2026-07-01T00:00:00+00:00",
            }
        ]
    )

    slack_ukos = [uko async for uko in slack.sync("eng")]
    confluence_ukos = [uko async for uko in confluence.sync("ENG")]

    assert slack_ukos[0].type == UKOType.MESSAGE
    assert confluence_ukos[0].type == UKOType.DOCUMENT


@pytest.mark.asyncio
async def test_identity_resolver_clusters_cross_system_people() -> None:
    created = datetime(2026, 7, 1, tzinfo=UTC)
    git_uko = UniversalKnowledgeObject(
        id="git:commit:1",
        type=UKOType.COMMIT,
        name="commit",
        metadata=UKOMetadata(
            source="git",
            source_id="1",
            created_at=created,
            modified_at=created,
            authors=["Brajesh Patil"],
        ),
    )
    jira_uko = UniversalKnowledgeObject(
        id="jira:ticket:ABC-1",
        type=UKOType.TICKET,
        name="ticket",
        metadata=UKOMetadata(
            source="jira",
            source_id="ABC-1",
            created_at=created,
            modified_at=created,
        ),
        relationships=[
            UKORelationship(target_id="B. Patil", relationship="assigned_to", target_type=UKOType.PERSON)
        ],
    )

    resolved = await IdentityResolver().resolve([git_uko, jira_uko])

    assert len(resolved) == 1
    assert resolved[0].type == UKOType.PERSON
    assert resolved[0].name == "Brajesh Patil"

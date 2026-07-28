from datetime import datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient

import ecms.api.graph_context as graph_context
from ecms.core.uko import UKOMetadata, UKOType, UniversalKnowledgeObject
from ecms.main import create_app
from ecms.providers.mysql import MySQLProvider
from ecms.providers.mysql.provider import MySQLConnectionConfig
from tests.fakes import FakeGraphClient


class FakeCursor:
    def __init__(self, responses: dict[str, list[dict[str, Any]]]) -> None:
        self.responses = responses
        self._rows: list[dict[str, Any]] = []

    def __enter__(self) -> "FakeCursor":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def execute(self, query: str, params: tuple | None = None) -> None:
        normalized = " ".join(query.lower().split())
        if "from information_schema.schemata" in normalized:
            self._rows = self.responses["schemata"]
        elif "from information_schema.tables" in normalized:
            self._rows = self.responses["tables"]
        elif "from information_schema.columns" in normalized:
            self._rows = self.responses["columns"]
        elif "from information_schema.key_column_usage" in normalized:
            self._rows = self.responses["foreign_keys"]
        else:
            raise AssertionError(f"Unexpected query: {query}")

    def fetchall(self) -> list[dict[str, Any]]:
        return self._rows


class FakeConnection:
    def __init__(self, responses: dict[str, list[dict[str, Any]]]) -> None:
        self.responses = responses

    def __enter__(self) -> "FakeConnection":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def cursor(self) -> FakeCursor:
        return FakeCursor(self.responses)


def fake_connection_factory(config: MySQLConnectionConfig) -> FakeConnection:
    assert config.host == "localhost"
    return FakeConnection(
        {
            "schemata": [{"schema_name": "billing"}],
            "tables": [
                {
                    "table_name": "orders",
                    "table_type": "BASE TABLE",
                    "create_time": datetime(2026, 7, 1, 10, 0, 0),
                    "update_time": datetime(2026, 7, 2, 10, 0, 0),
                    "table_comment": "Customer orders",
                }
            ],
            "columns": [
                {
                    "table_name": "orders",
                    "column_name": "id",
                    "column_type": "bigint",
                    "is_nullable": "NO",
                    "column_key": "PRI",
                    "column_default": None,
                    "extra": "auto_increment",
                    "ordinal_position": 1,
                    "column_comment": "",
                },
                {
                    "table_name": "orders",
                    "column_name": "customer_id",
                    "column_type": "bigint",
                    "is_nullable": "NO",
                    "column_key": "MUL",
                    "column_default": None,
                    "extra": "",
                    "ordinal_position": 2,
                    "column_comment": "",
                },
            ],
            "foreign_keys": [
                {
                    "table_name": "orders",
                    "column_name": "customer_id",
                    "referenced_table_schema": "billing",
                    "referenced_table_name": "customers",
                    "referenced_column_name": "id",
                    "constraint_name": "orders_customer_fk",
                }
            ],
        }
    )


@pytest.mark.asyncio
async def test_mysql_provider_discovers_and_syncs_live_schema() -> None:
    provider = MySQLProvider(connection_factory=fake_connection_factory)
    await provider.authenticate(
        {
            "host": "localhost",
            "port": 3306,
            "user": "ecms",
            "password": "secret",
            "database": "billing",
        }
    )

    assert await provider.validate()
    assert await provider.discover() == ["billing"]

    ukos = [uko async for uko in provider.sync("billing")]

    assert len(ukos) == 1
    assert ukos[0].type == UKOType.TABLE
    assert ukos[0].name == "billing.orders"
    assert "`customer_id` bigint NOT NULL" in ukos[0].content
    assert ukos[0].relationships[0].target_id == "billing.customers"
    assert ukos[0].raw_data["columns"][0]["name"] == "id"


def test_mysql_sync_api_does_not_echo_password(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_sync(self: MySQLProvider, resource_id: str, since=None):
        async def iterator():
            yield UniversalKnowledgeObject(
                id="mysql:table:billing.orders",
                type=UKOType.TABLE,
                name="billing.orders",
                content="CREATE TABLE orders (`id` bigint);",
                metadata=UKOMetadata(
                    source="mysql",
                    source_id="billing.orders",
                    created_at=datetime(2026, 7, 1),
                    modified_at=datetime(2026, 7, 1),
                    tags=["schema", "table"],
                ),
            )

        return iterator()

    monkeypatch.setattr(MySQLProvider, "sync", fake_sync)
    client = TestClient(create_app())

    response = client.post(
        "/providers/mysql/sync",
        json={
            "host": "localhost",
            "port": 3306,
            "user": "ecms",
            "password": "secret",
            "database": "billing",
        },
    )

    assert response.status_code == 200
    assert response.json()["uko_count"] == 1
    assert response.json()["persisted"] is False
    assert "secret" not in response.text


def test_mysql_sync_api_persists_when_requested(monkeypatch: pytest.MonkeyPatch) -> None:
    FakeGraphClient.reset()
    monkeypatch.setattr(graph_context, "create_graph_client", lambda: FakeGraphClient())

    def fake_sync(self: MySQLProvider, resource_id: str, since=None):
        async def iterator():
            yield UniversalKnowledgeObject(
                id="mysql:table:billing.orders",
                type=UKOType.TABLE,
                name="billing.orders",
                content="CREATE TABLE orders (`id` bigint);",
                metadata=UKOMetadata(
                    source="mysql",
                    source_id="billing.orders",
                    created_at=datetime(2026, 7, 1),
                    modified_at=datetime(2026, 7, 1),
                    tags=["schema", "table"],
                ),
            )

        return iterator()

    monkeypatch.setattr(MySQLProvider, "sync", fake_sync)
    client = TestClient(create_app())

    response = client.post(
        "/providers/mysql/sync",
        json={
            "host": "localhost",
            "port": 3306,
            "user": "ecms",
            "password": "secret",
            "database": "billing",
            "persist": True,
        },
    )

    assert response.status_code == 200
    assert response.json()["persisted"] is True
    assert len(FakeGraphClient.instances[0].episodes) == response.json()["episode_count"]

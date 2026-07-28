from typing import Any

import pytest
from legacy_ecms.core.graph import GraphClient


class FakeRawGraph:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def query(self, query: str, params: dict[str, Any]):
        self.calls.append((query, params))
        return []


@pytest.mark.asyncio
async def test_raw_batch_uses_unwind_for_nodes_and_relationships() -> None:
    graph = FakeRawGraph()
    batch = [
        {
            "id": "source",
            "name": "source.py",
            "type": "file",
            "layer": "evidence",
            "content": "content",
            "episode_name": "source.py",
            "source": "git",
            "source_id": "source.py",
            "source_description": "Git file",
            "source_url": "https://github.com/example/repo.git",
            "modified_at": "2026-07-28T00:00:00+00:00",
            "group_id": "",
            "status": "active",
            "provenance": {"confidence": 1.0},
            "organization_id": "org-1",
            "connection_id": "connection-1",
            "ingestion_revision": "abc123",
            "relationships": [
                {
                    "target_id": "target",
                    "target_type": "file",
                    "relationship": "imports",
                    "confidence": 1.0,
                    "metadata": {},
                    "provenance": {},
                }
            ],
        }
    ]

    result = await GraphClient._flush_raw_batch(graph, batch, schema_enforcement="off")

    assert result.success_count == 1
    assert result.failure_count == 0
    assert len(graph.calls) == 2
    assert graph.calls[0][0].startswith("UNWIND $rows AS row")
    assert graph.calls[1][0].startswith("UNWIND $rows AS row")
    assert graph.calls[0][1]["rows"][0]["ingestion_revision"] == "abc123"
    assert graph.calls[1][1]["rows"][0]["connection_id"] == "connection-1"

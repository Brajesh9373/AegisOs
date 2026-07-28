"""Integration tests for the cognition REST API (SECTION 92/193)."""

from __future__ import annotations

import httpx

from ecms.api.app import create_app


async def test_ingest_search_execute_and_graph() -> None:
    app = create_app()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        ingest = await client.post(
            "/api/v1/knowledge/ingest",
            json={
                "title": "auth.py",
                "content": "class AuthService(Base):\n    pass\n",
            },
        )
        assert ingest.status_code == 200
        assert ingest.json()["generated"] >= 1

        search = await client.get("/api/v1/knowledge/search", params={"q": "AuthService"})
        assert search.status_code == 200
        assert search.json()["results"]

        execute = await client.post("/api/v1/execute", json={"prompt": "AuthService"})
        assert execute.status_code == 200
        body = execute.json()
        assert body["status"] == "completed"
        assert body["activated_uco_ids"]

        stats = await client.get("/api/v1/graph/statistics")
        assert stats.status_code == 200
        assert "node_count" in stats.json()

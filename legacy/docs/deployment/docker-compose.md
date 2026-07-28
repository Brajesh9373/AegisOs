# ECMS Docker Compose Deployment

## Services

- `api`: FastAPI service for ingestion, provider catalog, memory, and query routes.
- `falkordb`: persistent property graph database used through Graphiti.
- `redis`: reserved for task queue and session memory backends.

## Start

```bash
docker compose up --build
```

## Initialize FalkorDB

```bash
docker compose exec api python scripts/init_falkordb.py
```

## Verify Graph Connectivity

```bash
curl http://localhost:8000/health/graph
```

Expected response:

```json
{
  "status": "ok",
  "graph": "graphiti-falkordb",
  "error": null
}
```

## Persist Ingestion

Provider sync routes default to dry-run mode. Set `persist` to `true` to write generated episodes into Graphiti/FalkorDB.

```bash
curl -X POST http://localhost:8000/providers/git/sync \
  -H "Content-Type: application/json" \
  -d '{"repo_url":"https://github.com/acme/payments","access_token":"token-value","persist":true}'
```

## Production Notes

- Set `AUTH_ENABLED=true` and rotate `API_KEY`.
- Set `OPENAI_API_KEY`, `OPENAI_BASE_URL`, and model variables before enabling Graphiti-backed persistence with a compatible LLM provider.
- Mount durable volumes for `falkordb_data`, `redis_data`, `data`, and `memory`.
- Use one FalkorDB graph/database name per tenant when multi-tenancy is enabled.

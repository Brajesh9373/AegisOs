# ECMS Enterprise Cognitive Memory System

The complete documentation for the Enterprise Cognitive Memory System — a
cognitive operating system that ingests, understands, organizes, and activates
enterprise knowledge.

## Quick Links

| Document | What It Covers |
|----------|---------------|
| [Architecture](architecture.md) | Full system overview — 14 services, 6 storage backends, data flow |
| [Backend Architecture](backend-architecture.md) | Code layout, request flow, cognitive pipeline, dual codebase |
| [Memory Architecture](memory.md) | All 10 memory tiers, how they connect, workspace scoping |
| [Memory Implementation](memory-implementation.md) | Code internals — agent loop, search, extraction, sync, cascade delete |

## Getting Started

```bash
# Offline dev (zero external services)
cd backend && uv sync && uv run uvicorn ecms.main:app --reload
cd frontend && pnpm install && pnpm dev

# Full stack (all 14 services)
docker compose -f docker/docker-compose.yml up --build
```

Backend: `http://localhost:8000` | Frontend: `http://localhost:3000` | Grafana: `http://localhost:3300`

## Repository

[`github.com/navadhan/ecms`](https://github.com/navadhan/ecms)

## System Snapshot

- **Services:** 18+ Docker containers
- **Storage:** PostgreSQL, FalkorDB, Qdrant, Redis, MinIO
- **Backend:** Python 3.12 + FastAPI + GraphQL + WebSocket + SSE
- **Frontend:** React 18 + TypeScript + Vite + Ant Design
- **Cognition:** Knowledge Engine, Global Graph, Memory Tiers, Runtime Kernel, ReAct Agent Loop
- **Observability:** Prometheus + Grafana + Loki + Tempo + OpenTelemetry

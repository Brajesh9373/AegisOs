# AegisOS Deployment Guide

This guide covers every deployment path for the AegisOS platform: local development, Docker Compose production, Kubernetes (Kustomize and Helm), Terraform provisioning, CI/CD, and webhook-based continuous deployment.

---

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.12 | Backend runtime |
| Node.js | 20 LTS | Frontend build, JS/TS analysis in containers |
| pnpm | 9+ | Frontend dependency management |
| Docker | 24+ | Container runtime |
| Docker Compose | v2 | Multi-service orchestration |
| uv | latest | Python dependency management (replaces pip in dev) |
| Helm | 3.x | Kubernetes chart deployment |
| Terraform | >= 1.5 | Infrastructure provisioning |
| kubectl | latest | Kubernetes cluster access |

---

## Local Development

### Quick start with Docker Compose (dev)

```bash
cd /path/to/ecms
docker compose -f docker/docker-compose.yml up --build
```

This brings up the full stack: PostgreSQL, Redis, FalkorDB, Qdrant, MinIO, Prometheus, Loki, Tempo, Grafana, the backend API, all workers, and the frontend. Ports are exposed on localhost for direct access.

To use pre-built images instead of building locally:

1. Comment out the `build:` sections in `docker/docker-compose.yml`
2. Uncomment the `image:` lines above them
3. Run `docker compose -f docker/docker-compose.yml up -d`

### Backend development (without Docker)

```bash
cd backend
uv sync
uv run alembic upgrade head
uv run uvicorn ecms.main:app --reload --host 0.0.0.0 --port 8000
```

The backend expects these services to be reachable at their default localhost ports:
- PostgreSQL on `5432`
- Redis on `6379`
- FalkorDB on `6380`
- MinIO on `9000`
- Qdrant on `6333`

Set `ECMS_DATABASE_URL=postgresql+asyncpg://ecms:ecms@localhost:5432/ecms` and adjust other `ECMS_*` variables accordingly.

### Frontend development

```bash
cd frontend
pnpm install
pnpm run dev        # Vite dev server on port 5173
pnpm run typecheck  # Type checking
pnpm run build      # Production build
```

The Vite dev server proxies `/api` requests to the backend at `localhost:8000`.

---

## Docker Compose Production

The production compose file is `docker/docker-compose.prod.yml`. It differs from the dev file in several important ways:

- **No exposed ports** on infrastructure services (Postgres, Redis, FalkorDB, etc.) -- they are only reachable within the Docker network.
- **Digest-pinned images** for all infrastructure: FalkorDB, Qdrant, MinIO, Prometheus, Loki, Tempo, and Grafana all require explicit image references via environment variables (e.g., `FALKORDB_IMAGE`, `QDRANT_IMAGE`). The compose file will refuse to start if any are missing.
- **Required secrets** via environment variables: `POSTGRES_PASSWORD`, `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`, `GRAFANA_ADMIN_PASSWORD`, `ECMS_CORS_ALLOW_ORIGINS`, `ECMS_S3_PUBLIC_ENDPOINT_URL`, `ECMS_OPENAI_API_KEY`, `ECMS_CATEGORIZE_API_KEY`, `COMMAND_CODE_API_KEY`.
- **Grafana anonymous auth disabled** (`GF_AUTH_ANONYMOUS_ENABLED: "false"`).
- **Grafana bound to localhost only** (`127.0.0.1:3300:3000`).

### Running production

Create a `.env` file in the `docker/` directory (or export variables):

```bash
# Required
POSTGRES_PASSWORD=<strong-password>
MINIO_ROOT_USER=<access-key>
MINIO_ROOT_PASSWORD=<secret-key>
GRAFANA_ADMIN_PASSWORD=<admin-password>
ECMS_CORS_ALLOW_ORIGINS=https://yourdomain.com
ECMS_S3_PUBLIC_ENDPOINT_URL=https://your-cdn.example.com

# Digest-pinned infrastructure images
FALKORDB_IMAGE=falkordb/falkordb@sha256:<digest>
QDRANT_IMAGE=qdrant/qdrant@sha256:<digest>
MINIO_IMAGE=minio/minio@sha256:<digest>
MINIO_MC_IMAGE=minio/mc@sha256:<digest>
PROMETHEUS_IMAGE=prom/prometheus@sha256:<digest>
LOKI_IMAGE=grafana/loki@sha256:<digest>
TEMPO_IMAGE=grafana/tempo@sha256:<digest>
GRAFANA_IMAGE=grafana/grafana@sha256:<digest>

# API keys
ECMS_OPENAI_API_KEY=<key>
COMMAND_CODE_API_KEY=<key>
ECMS_CATEGORIZE_API_KEY=<key>
```

```bash
docker compose -f docker/docker-compose.prod.yml up -d --build
```

### Docker Compose profiles

The `parallel-ingestion` profile gates the extractor and graph-writer services. They are not started by default. To enable the parallel ingestion pipeline:

```bash
docker compose -f docker/docker-compose.prod.yml --profile parallel-ingestion up -d
```

This starts `connector-ingestion-extractor` and `connector-ingestion-graph-writer` in addition to the default `connector-ingestion-worker` (parent dispatcher).

---

## Container Architecture

The platform runs 18+ containers in a full deployment. Here is every service, its image, role, and resource limits.

### Data stores

| Service | Image | Port | Role | Resource limits |
|---------|-------|------|------|-----------------|
| `postgres` | `postgres:16-alpine` | 5432 | Primary relational database (asyncpg) | -- |
| `redis` | `redis:7-alpine` | 6379 | Caching, durable snapshot jobs | -- |
| `falkordb` | `falkordb/falkordb` | 6379 (internal), 3000 (UI) | Graph database (Redis protocol) | 1 CPU, 2 GB RAM |
| `qdrant` | `qdrant/qdrant` | 6333 (HTTP), 6334 (gRPC) | Vector database for mem0 embeddings | -- |
| `minio` | `minio/minio` | 9000 (API), 9001 (console) | S3-compatible object storage | -- |
| `minio-init` | `minio/mc` | -- | One-shot: creates `ecms-knowledge-graph` bucket | -- |

### Application services

| Service | Command | Port | Role | Resource limits |
|---------|---------|------|------|-----------------|
| `backend` | `/entrypoint.sh` (uvicorn) | 8000 | REST API gateway, GraphQL, WebSocket, SSE streaming | -- |
| `frontend` | `nginx -g daemon off` | 80 (mapped to 3000) | SPA static files, nginx reverse proxy to backend | -- |
| `telegram-bot` | `python -m ecms.telegram` | -- | Telegram bot interface | -- |

### Workers

| Service | Command | Role |
|---------|---------|------|
| `knowledge-snapshot-worker` | `python -m ecms.visualization.snapshot_worker` | Builds immutable knowledge-graph snapshots to S3 |
| `worker-knowledge` | `ecms.cli.app worker knowledge` | Knowledge processing worker |
| `worker-reflection` | `ecms.cli.app worker reflection` | Reflection processing worker |
| `worker-promotion` | `ecms.cli.app worker promotion` | Promotion processing worker |

### Connector ingestion pipeline

| Service | Command | Profile | Resource limits |
|---------|---------|---------|-----------------|
| `connector-ingestion-init` | `mkdir -p /workspace/connector-ingestions` | default | -- |
| `connector-ingestion-worker` | `ecms.connectors.ingestion.parent_dispatcher` | default | 0.75 CPU, 2 GB RAM |
| `connector-ingestion-extractor` | `ecms.connectors.ingestion.extraction_process` | `parallel-ingestion` | 0.75 CPU, 2 GB RAM |
| `connector-ingestion-graph-writer` | `ecms.connectors.ingestion.graph_writer_process` | `parallel-ingestion` | 0.5 CPU, 1 GB RAM |

### Observability stack

| Service | Image | Port | Role |
|---------|-------|------|------|
| `prometheus` | `prom/prometheus` | 9090 | Metrics scraping and alerting |
| `loki` | `grafana/loki` | 3100 | Log aggregation |
| `tempo` | `grafana/tempo` | 3200 (HTTP), 4317 (OTLP gRPC) | Distributed tracing |
| `grafana` | `grafana/grafana` | 3300 (mapped from 3000) | Dashboards for Prometheus, Loki, Tempo |

Prometheus scrapes the backend at `backend:8000/metrics` every 15 seconds. Alert rules live in `docker/prometheus/knowledge-graph-alerts.yml` and `docker/prometheus/connector-ingestion-alerts.yml`.

### Docker volumes

| Volume | Purpose |
|--------|---------|
| `postgres_data` | PostgreSQL data directory |
| `redis_data` | Redis persistence |
| `falkordb_data` | FalkorDB graph storage |
| `qdrant_data` | Qdrant vector storage |
| `minio_data` | MinIO object storage |
| `memory_data` | mem0 memory persistence (`/app/memory`) |
| `repos_data` | Cloned repository cache (`/app/data/repos`) |
| `connector_ingestion_data` | Shared workspace for connector ingestion pipeline |

### Entrypoint sequence

The backend container entrypoint (`scripts/entrypoint.sh`) performs these steps in order:

1. Runs Alembic database migrations (`alembic upgrade head`)
2. Ensures `/workspace/uploads` exists with correct ownership
3. Starts uvicorn on `0.0.0.0:8000`

---

## Container Image: Backend Dockerfile

`docker/backend.Dockerfile` is a multi-stage build:

**Stage 1 (builder):** Python 3.12-slim, installs uv, syncs backend dependencies from `pyproject.toml`/`uv.lock`, installs fastembed and python-telegram-bot.

**Stage 2 (runtime):** Python 3.12-slim with Git, Node.js 20, redis-tools, acorn (JS parser), and command-code CLI. Copies the backend code, legacy providers, Alembic config, and deployment manifests. Runs as the `ecms` user (UID 1000). Bundles the production compose file and observability configs into `/deploy/` for extraction via `docker run --rm brajesh07/ecms-backend:latest cat /deploy/docker-compose.prod.yml`.

Health check: `GET /health` every 30 seconds, 5-second timeout, 15-second start period, 3 retries.

### Frontend Dockerfile

`docker/frontend.Dockerfile` is a two-stage build: Node 20 + pnpm 9 builds the Vite app, then nginx:alpine serves the static files. Health check: `wget -qO- http://localhost:80/health` every 30 seconds.

---

## Kubernetes Deployment

### Kustomize base

The base manifests live in `kubernetes/base/` and are applied with:

```bash
kubectl apply -k kubernetes/base/
```

This creates:

- **Namespace** `ecms` with label `app.kubernetes.io/name: ecms`
- **ConfigMap** `ecms-backend-config` with `ECMS_ENVIRONMENT=production` and `ECMS_LOG_LEVEL=INFO`
- **Backend Deployment** (2 replicas, RollingUpdate with maxSurge=1, maxUnavailable=0)
  - Liveness probe: `GET /health` on port 8000, initial delay 10s, period 15s
  - Readiness probe: `GET /ready` on port 8000, initial delay 5s, period 10s
  - PreStop hook: `sleep 5` (graceful drain)
  - Resources: requests 100m CPU / 256Mi RAM, limits 1 CPU / 512Mi RAM
  - SecurityContext: runAsNonRoot, runAsUser 1000
  - terminationGracePeriodSeconds: 30
- **Backend Service** on port 80 -> targetPort 8000
- **Backend HPA** (autoscaling/v2): min 2, max 10 replicas, target 70% CPU utilization
- **Frontend Deployment** (2 replicas, same rolling update strategy)
  - Resources: requests 50m CPU / 128Mi RAM, limits 500m CPU / 256Mi RAM
- **Frontend Service** on port 80 -> targetPort 3000
- **Ingress** (nginx class):
  - `/api` and `/graphql` -> ecms-backend:80
  - `/` -> ecms-frontend:80

### Helm chart

The Helm chart at `kubernetes/helm/ecms/` provides templated manifests with configurable values.

```bash
helm install ecms kubernetes/helm/ecms/ \
  --namespace ecms \
  --create-namespace \
  --set backend.image=brajesh07/ecms-backend:v1.2.3 \
  --set frontend.image=brajesh07/ecms-frontend:v1.2.3 \
  --set ingress.host=ecms.yourdomain.com \
  --set config.ECMS_OPENAI_API_KEY=<key>
```

Key `values.yaml` defaults:

| Value | Default |
|-------|---------|
| `namespace` | `ecms` |
| `backend.image` | `ecms-backend:latest` |
| `backend.replicas` | 2 |
| `backend.port` | 8000 |
| `backend.autoscaling.enabled` | true |
| `backend.autoscaling.minReplicas` | 2 |
| `backend.autoscaling.maxReplicas` | 10 |
| `backend.autoscaling.targetCPUUtilizationPercentage` | 70 |
| `frontend.image` | `ecms-frontend:latest` |
| `frontend.replicas` | 2 |
| `frontend.port` | 3000 |
| `ingress.enabled` | true |
| `ingress.className` | nginx |
| `ingress.host` | `ecms.local` |
| `config.ECMS_ENVIRONMENT` | `production` |
| `config.ECMS_LOG_LEVEL` | `INFO` |

The ConfigMap template iterates over all keys in `config`, so you can pass arbitrary `ECMS_*` variables via `--set config.ECMS_<KEY>=<value>`.

---

## Terraform Provisioning

The Terraform module at `terraform/` provisions the Kubernetes namespace and backend ConfigMap.

```bash
cd terraform
terraform init
terraform plan -var="environment=production"
terraform apply -var="environment=production"
```

### Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `kubeconfig_path` | string | `~/.kube/config` | Path to kubeconfig |
| `namespace` | string | `ecms` | Kubernetes namespace |
| `environment` | string | `production` | Deployment environment label |

### Outputs

| Output | Description |
|--------|-------------|
| `namespace` | The created namespace name |
| `backend_config_map` | The ConfigMap name (`ecms-backend-config`) |

### Provider requirements

- Terraform >= 1.5
- hashicorp/kubernetes ~> 2.30

After Terraform creates the namespace and ConfigMap, deploy the application with either Kustomize or Helm.

---

## CI/CD Pipeline

### GitHub Actions (`.github/workflows/ci.yml`)

The CI pipeline runs on every push to `main` and every pull request. It contains 7 jobs:

| Job | What it does |
|-----|--------------|
| `backend` | uv sync, ruff lint, ruff format check, mypy type check, pytest, benchmarks |
| `security` | ruff security rules (SAST), pip-audit dependency scan |
| `frontend` | pnpm install (frozen lockfile), typecheck, Vite build |
| `docker` | Builds the backend Docker image (no push, validation only) |
| `kubernetes` | kubeconform validation of base manifests, helm lint, helm template + kubeconform |
| `terraform` | terraform fmt check, init (no backend), validate |
| `docs` | mkdocs build with `--strict` |

All backend jobs use `astral-sh/setup-uv@v5` with Python 3.12. Frontend jobs use `pnpm/action-setup@v4` with pnpm 10 and `actions/setup-node@v4` with Node 20.

### Dependabot

Dependabot is configured to keep dependencies up to date. PRs are validated by the full CI pipeline before merge.

---

## Webhook-Based Continuous Deployment

### Architecture

A GitHub webhook fires on every push to `main`. The webhook listener (`scripts/webhook_listener.py`) verifies the HMAC-SHA256 signature, checks the event is a push to `refs/heads/main`, and triggers `scripts/deploy.sh`.

### Webhook listener

- Listens on port `9100` at `/webhook`
- Verifies `X-Hub-Signature-256` header against `WEBHOOK_SECRET` env var
- Health check at `GET /health`
- Logs to `/home/ubuntu/ecms/logs/webhook.log`
- 300-second timeout on the deploy subprocess

### Deploy script (smart incremental deploy)

`scripts/deploy.sh` performs a lock-guarded, incremental deployment:

1. **Lock file** (`/home/ubuntu/ecms/.deploy.lock`) prevents concurrent deploys
2. **Git fetch + diff** -- compares local HEAD to `origin/main`; skips if already up to date
3. **Change detection** -- scans changed files to decide what to rebuild:
   - `backend/*` changes -> rebuild backend + run migrations
   - `frontend/*` changes -> rebuild frontend
   - `docker/*` or `scripts/*` changes -> rebuild both + run migrations
4. **Conditional migration** -- runs `alembic upgrade head` inside the running backend container
5. **Conditional backend rebuild** -- `docker compose up -d --build --no-deps backend`
6. **Conditional frontend rebuild** -- `docker compose up -d --build --no-deps frontend`
7. **Nginx reload** -- picks up any config changes
8. Logs the deployed commit SHA

### Setting up the webhook

1. Run the listener on your server (e.g., via systemd)
2. In GitHub repo settings, add a webhook:
   - Payload URL: `http://your-server:9100/webhook`
   - Content type: `application/json`
   - Secret: same as `WEBHOOK_SECRET` env var
   - Events: `Just the push event`

---

## Environment Variables Reference

All application settings use the `ECMS_` prefix and are loaded by `pydantic-settings` in `backend/ecms/configuration/schemas/settings.py`.

### Core

| Variable | Default | Description |
|----------|---------|-------------|
| `ECMS_ENVIRONMENT` | `development` | Deployment profile: `development`, `testing`, `staging`, `production` |
| `ECMS_LOG_LEVEL` | `INFO` | Root logging level |
| `ECMS_DEBUG` | `false` | Enable verbose debug behavior |
| `ECMS_RATE_LIMIT_PER_MINUTE` | `1000` | Max requests per client per minute |
| `ECMS_CONFIG_DIR` | `config` | Directory for layered config files |

### CORS

| Variable | Default | Description |
|----------|---------|-------------|
| `ECMS_CORS_ALLOW_ORIGINS` | `http://localhost:3000,http://localhost:5173,http://localhost:5174` | Comma-separated trusted origins |
| `ECMS_CORS_ALLOW_CREDENTIALS` | `true` | Allow credentials in CORS requests |
| `ECMS_CORS_ALLOW_METHODS` | `*` | Allowed HTTP methods |
| `ECMS_CORS_ALLOW_HEADERS` | `*` | Allowed request headers |

### Database and cache

| Variable | Default | Description |
|----------|---------|-------------|
| `ECMS_DATABASE_URL` | -- | PostgreSQL connection string (asyncpg) |
| `ECMS_REDIS_URL` | `redis://localhost:6380/0` | Redis URL for caching |
| `ECMS_FALKORDB_URL` | `redis://localhost:6379` | FalkorDB graph database URL |
| `ECMS_FALKORDB_GRAPH` | `ecms` | Graph name within FalkorDB |

### S3 / Object storage

| Variable | Default | Description |
|----------|---------|-------------|
| `ECMS_S3_ENDPOINT_URL` | `null` | S3-compatible endpoint (null for AWS S3) |
| `ECMS_S3_PUBLIC_ENDPOINT_URL` | `null` | Browser-reachable S3/CDN endpoint for signed downloads |
| `ECMS_S3_REGION` | `us-east-1` | S3 region |
| `ECMS_S3_BUCKET` | `ecms-knowledge-graph` | Bucket for knowledge-graph snapshots |
| `ECMS_S3_ACCESS_KEY` | -- | S3 access key |
| `ECMS_S3_SECRET_KEY` | -- | S3 secret key |

### Knowledge graph

| Variable | Default | Description |
|----------|---------|-------------|
| `ECMS_KNOWLEDGE_GRAPH_RENDERER` | `d3` | Renderer: `d3` or `cosmos` |
| `ECMS_KNOWLEDGE_GRAPH_COSMOS_ROLES` | `Super Admin,Administrator,Admin` | Roles enabled for Cosmos renderer |
| `ECMS_KNOWLEDGE_GRAPH_MAX_CLIENT_NODES` | `100000` | Max nodes for interactive browser snapshot |
| `ECMS_KNOWLEDGE_GRAPH_MAX_CLIENT_LINKS` | `200000` | Max edges for interactive browser snapshot |
| `ECMS_KNOWLEDGE_GRAPH_BUILD_START_DELAY_SECONDS` | `0` | Chaos-test delay (must be 0 in production) |

### LLM and embeddings

| Variable | Default | Description |
|----------|---------|-------------|
| `ECMS_LLM_MODEL` | -- | LLM model identifier |
| `ECMS_EMBEDDING_MODEL` | -- | Embedding model identifier |
| `ECMS_EMBEDDING_DIM` | `1536` | Embedding dimensions |
| `ECMS_OPENAI_API_KEY` | -- | OpenAI-compatible API key |
| `ECMS_OPENAI_BASE_URL` | -- | OpenAI-compatible base URL |
| `ECMS_CATEGORIZE_MODEL` | -- | Categorization model |
| `ECMS_CATEGORIZE_API_KEY` | -- | Categorization API key |
| `ECMS_CATEGORIZE_BASE_URL` | -- | Categorization base URL |

### mem0

| Variable | Default | Description |
|----------|---------|-------------|
| `ECMS_MEM0_ENABLED` | `false` | Enable mem0 memory system |
| `ECMS_MEM0_QDRANT_HOST` | -- | Qdrant host |
| `ECMS_MEM0_QDRANT_PORT` | `6333` | Qdrant port |
| `ECMS_MEM0_QDRANT_PATH` | -- | Qdrant storage path |
| `ECMS_MEM0_HOME_PATH` | -- | mem0 home directory |

### Connector ingestion

| Variable | Default | Description |
|----------|---------|-------------|
| `ECMS_CONNECTOR_INGESTION_ENABLED` | `true` | Enable connector ingestion |
| `ECMS_CONNECTOR_PARALLEL_INGESTION_ENABLED` | `false` | Enable parallel fan-out pipeline |
| `ECMS_CONNECTOR_EXTRACTION_WORKER_COUNT` | `4` | Extraction lanes (1--64) |
| `ECMS_CONNECTOR_GRAPH_WRITER_CONCURRENCY` | `1` | Graph-writer replica ceiling (1--8, must be 1 with parallel ingestion) |
| `ECMS_CONNECTOR_INGESTION_WORKSPACE` | `/workspace/connector-ingestions` | Shared workspace path |
| `ECMS_CONNECTOR_INGESTION_PARTITION_TARGET_FILES` | `100` | Target files per partition |
| `ECMS_CONNECTOR_INGESTION_MAX_ACTIVE_PARTITIONS_PER_ORG` | `8` | Max concurrent partitions per org |
| `ECMS_CONNECTOR_INGESTION_MAX_STAGED_BYTES_PER_ORG` | `10737418240` (10 GB) | Max staged bytes per org |
| `ECMS_CONNECTOR_INGESTION_MAX_BATCH_ENCODED_BYTES` | `4194304` (4 MB) | Max batch size |
| `ECMS_CONNECTOR_INGESTION_CHUNK_SIZE` | `10` | Chunk size for processing |
| `ECMS_CONNECTOR_INGESTION_WRITE_YIELD_SECONDS` | `0.1` | Yield between writes |
| `ECMS_CONNECTOR_INGESTION_MAX_FILES` | `250000` | Max files per ingestion |
| `ECMS_CONNECTOR_INGESTION_MAX_FILE_BYTES` | `2097152` (2 MB) | Max single file size |
| `ECMS_CONNECTOR_INGESTION_MAX_TOTAL_BYTES` | `2147483648` (2 GB) | Max total ingestion size |
| `ECMS_CONNECTOR_INGESTION_MAX_DELIVERIES` | `3` | Max delivery attempts |
| `ECMS_CONNECTOR_INGESTION_STALE_AFTER_SECONDS` | `120` | Stale threshold |
| `ECMS_CONNECTOR_INGESTION_STAGED_RETENTION_DAYS` | `7` | Retention before cleanup |
| `ECMS_CONNECTOR_GIT_CLONE_DEPTH` | `50` | Git clone depth |
| `ECMS_CONNECTOR_GIT_CLONE_TIMEOUT_SECONDS` | `600` | Clone timeout |
| `ECMS_CONNECTOR_GIT_FETCH_TIMEOUT_SECONDS` | `300` | Fetch timeout |
| `ECMS_CONNECTOR_INGESTION_SNAPSHOT_TIMEOUT_SECONDS` | `1800` | Snapshot timeout |
| `ECMS_CONNECTOR_WORKER_ROLE` | -- | Worker role: `parent`, `extractor`, `graph-writer` |

### Observability

| Variable | Default | Description |
|----------|---------|-------------|
| `ECMS_OTEL_ENDPOINT` | -- | OpenTelemetry collector endpoint (gRPC) |

### External integrations

| Variable | Default | Description |
|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | -- | Telegram bot token |
| `TELEGRAM_MANAGER_CHAT_ID` | -- | Telegram manager chat ID |
| `COMMAND_CODE_API_KEY` | -- | Command Code API key |
| `ECMS_CLI_BINARY` | `command-code` | CLI binary name |

### Resource limits (Docker Compose)

| Variable | Default | Description |
|----------|---------|-------------|
| `ECMS_FALKORDB_CPU_LIMIT` | `1.0` | FalkorDB CPU limit |
| `ECMS_FALKORDB_MEMORY_LIMIT` | `2g` | FalkorDB memory limit |
| `ECMS_CONNECTOR_INGESTION_CPU_LIMIT` | `0.75` | Connector worker CPU limit |
| `ECMS_CONNECTOR_INGESTION_MEMORY_LIMIT` | `2g` | Connector worker memory limit |
| `ECMS_CONNECTOR_EXTRACTION_CPU_LIMIT` | `0.75` | Extractor CPU limit |
| `ECMS_CONNECTOR_EXTRACTION_MEMORY_LIMIT` | `2g` | Extractor memory limit |
| `ECMS_CONNECTOR_GRAPH_WRITER_CPU_LIMIT` | `0.5` | Graph-writer CPU limit |
| `ECMS_CONNECTOR_GRAPH_WRITER_MEMORY_LIMIT` | `1g` | Graph-writer memory limit |

---

## Port Map

### Host-accessible ports (dev compose)

| Port | Service | Protocol |
|------|---------|----------|
| 3000 | Frontend (nginx) | HTTP |
| 3300 | Grafana | HTTP |
| 5432 | PostgreSQL | TCP |
| 6333 | Qdrant HTTP | HTTP |
| 6334 | Qdrant gRPC | gRPC |
| 6379 | Redis | TCP |
| 6380 | FalkorDB | TCP |
| 9000 | MinIO API | HTTP |
| 9001 | MinIO Console | HTTP |
| 9090 | Prometheus | HTTP |
| 9092 | Kafka | TCP |
| 9100 | Webhook listener | HTTP |
| 3100 | Loki | HTTP |
| 3200 | Tempo HTTP | HTTP |
| 4317 | Tempo OTLP gRPC | gRPC |
| 8000 | Backend API | HTTP |

### Production compose

Only ports 3000 (frontend) and 3300 (Grafana, bound to 127.0.0.1) are exposed. All other services are internal to the Docker network.

### Kubernetes (Ingress)

| Path | Backend Service | Port |
|------|----------------|------|
| `/api/*` | ecms-backend | 80 |
| `/graphql` | ecms-backend | 80 |
| `/*` | ecms-frontend | 80 |

---

## Health Checks and Readiness Probes

### Backend

| Check | Endpoint | Interval | Timeout | Start period | Retries |
|-------|----------|----------|---------|--------------|---------|
| Docker HEALTHCHECK | `GET /health` | 30s | 5s | 15s | 3 |
| K8s liveness | `GET /health:8000` | 15s | -- | initialDelay 10s | -- |
| K8s readiness | `GET /ready:8000` | 10s | -- | initialDelay 5s | -- |

### Frontend

| Check | Endpoint | Interval | Timeout | Start period | Retries |
|-------|----------|----------|---------|--------------|---------|
| Docker HEALTHCHECK | `GET /health` | 30s | 5s | 10s | 3 |

### Connector ingestion workers

| Check | Endpoint | Interval | Timeout | Start period | Retries |
|-------|----------|----------|---------|--------------|---------|
| All workers | `ecms.connectors.ingestion.parallel_health` | 15s | 5s | 30s | 4 |

### Knowledge snapshot worker

| Check | Endpoint | Interval | Timeout | Retries |
|-------|----------|----------|---------|---------|
| Prod | `ecms.visualization.worker_health` | 15s | 5s | 3 |
| Dev | disabled | -- | -- | -- |

### Infrastructure

| Service | Check command | Interval |
|---------|--------------|----------|
| PostgreSQL | `pg_isready -U ecms` | 10s |
| Redis | `redis-cli ping` | 10s |
| FalkorDB | `redis-cli ping` | 10s |
| Qdrant (prod) | `bash -c ':> /dev/tcp/127.0.0.1/6333'` | 10s |
| MinIO | `mc ready local` | 15s |

---

## Scaling Guidelines

### Backend replicas

The Kubernetes HPA scales the backend between 2 and 10 replicas based on 70% average CPU utilization. Each replica runs uvicorn and handles REST, GraphQL, and WebSocket traffic. The rolling update strategy (maxSurge=1, maxUnavailable=0) ensures zero-downtime deploys.

To adjust:

```bash
kubectl patch hpa ecms-backend -n ecms -p '{"spec":{"maxReplicas":20}}'
```

Or in Helm:

```bash
helm upgrade ecms kubernetes/helm/ecms/ --set backend.autoscaling.maxReplicas=20
```

### Connector ingestion workers

The connector ingestion pipeline has three scaling dimensions:

1. **Parent dispatcher** (`connector-ingestion-worker`): 1 instance. It polls for new ingestion jobs and dispatches them. Do not scale horizontally -- it uses a distributed lock.

2. **Extractor** (`connector-ingestion-extractor`): Scale to match `ECMS_CONNECTOR_EXTRACTION_WORKER_COUNT` (default 4). Each extractor processes one partition at a time. The worker count in the config should match the number of running extractor replicas.

3. **Graph writer** (`connector-ingestion-graph-writer`): The current qualified topology supports exactly 1 globally serialized writer (`ECMS_CONNECTOR_GRAPH_WRITER_CONCURRENCY=1`). Scaling beyond 1 is not yet supported with parallel ingestion enabled.

Resource defaults:
- Parent dispatcher: 0.75 CPU, 2 GB RAM
- Extractor: 0.75 CPU, 2 GB RAM per instance
- Graph writer: 0.5 CPU, 1 GB RAM

The `stop_grace_period` for extractors is 30s; for graph-writers it is 60s (longer because graph commits need time to complete).

### Frontend replicas

Default 2 replicas in Kubernetes. The frontend is stateless nginx serving static files -- scale freely. Resource footprint is small (50m CPU / 128Mi RAM per pod).

---

## Rollback Procedures

### Docker Compose

```bash
# Revert to a previous image tag
docker compose -f docker/docker-compose.prod.yml up -d --no-deps backend
# Or pull and restart from a known-good image
docker compose -f docker/docker-compose.prod.yml pull backend
docker compose -f docker/docker-compose.prod.yml up -d --no-deps backend
```

For database rollbacks:

```bash
# Downgrade one migration
docker compose exec backend alembic downgrade -1

# Downgrade to a specific revision
docker compose exec backend alembic downgrade <revision>
```

### Kubernetes (Kustomize)

```bash
# View rollout history
kubectl rollout history deployment/ecms-backend -n ecms

# Rollback to previous revision
kubectl rollout undo deployment/ecms-backend -n ecms

# Rollback to a specific revision
kubectl rollout undo deployment/ecms-backend -n ecms --to-revision=2
```

### Kubernetes (Helm)

```bash
# View Helm release history
helm history ecms -n ecms

# Rollback to a previous release
helm rollback ecms <revision> -n ecms
```

### Git-based rollback (webhook deploy)

```bash
# On the server
cd /home/ubuntu/ecms
git log --oneline -10          # find the last good commit
git checkout <good-commit>     # move HEAD
# The next webhook push or manual trigger will deploy this state
# Or trigger manually:
bash scripts/deploy.sh
```

The deploy script's incremental logic means a rollback that only touches backend code will only rebuild the backend container, leaving the frontend untouched.

### Knowledge graph renderer rollback

If the Cosmos renderer causes issues, set `ECMS_KNOWLEDGE_GRAPH_RENDERER=d3` to fall back to the D3 renderer. This is a runtime setting and does not require a rebuild.

---

## Nginx Reverse Proxy

The frontend container runs nginx with a custom config (`docker/nginx.conf`) that:

- Serves the SPA with `try_files $uri $uri/ /index.html`
- Proxies `/api/` to the backend with SSE support (buffering off, 300s read timeout)
- Proxies `/graphql`, `/ws` (WebSocket), `/providers/` (600s timeout for long operations), `/legacy-graph/`, `/health`, `/agents`, `/categories`, `/projects`, `/organization/`, `/queue`
- Caches knowledge-graph snapshot artifacts from MinIO (`/ecms-knowledge-graph/`) with a 2 GB cache, 5-minute TTL
- Caches static assets (`/assets/`) for 1 year with immutable headers
- Enables gzip compression for text, JSON, JS, CSS, XML, SVG

The upstream `ecms_backend` uses Docker's internal DNS resolver (`127.0.0.11`) for dynamic service discovery.

---

## Secrets Management

Production secrets should never be committed to the repository. Options:

1. **Docker Compose**: Use a `.env` file (git-ignored) or export variables before `docker compose up`.
2. **Kubernetes**: Use Secrets objects referenced from the Deployment, or an external secrets operator (Vault, AWS Secrets Manager, etc.). The current base manifests use ConfigMap for non-sensitive config; extend with `secretRef` for credentials.
3. **Terraform**: Pass secrets via `-var` flags, `terraform.tfvars` (git-ignored), or a secrets manager provider.

The production compose file uses `${VAR:?error message}` syntax to fail fast if required secrets are missing.

---

## Observability

### Prometheus

Scrapes `backend:8000/metrics` every 15 seconds. Alert rules:
- `docker/prometheus/knowledge-graph-alerts.yml` -- knowledge-graph build and snapshot alerts
- `docker/prometheus/connector-ingestion-alerts.yml` -- connector ingestion pipeline alerts

### Loki

Collects logs from all containers. Configured via `docker/loki/loki-config.yml`.

### Tempo

Receives OpenTelemetry traces on port 4317 (gRPC). The backend sends traces to `http://tempo:4317` via `ECMS_OTEL_ENDPOINT`.

### Grafana

Dashboards auto-provisioned from `docker/grafana/provisioning/`. Data sources: Prometheus, Loki, Tempo. In production, anonymous access is disabled; set `GRAFANA_ADMIN_PASSWORD` securely.

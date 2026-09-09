# syntax=docker/dockerfile:1
# Multi-stage build for the ECMS backend gateway + legacy providers (SECTION 17/106).

FROM python:3.12-slim AS builder
ENV UV_LINK_MODE=copy \
    PYTHONDONTWRITEBYTECODE=1
RUN pip install --no-cache-dir uv
WORKDIR /app
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --no-dev --frozen --no-install-project
RUN .venv/bin/pip install --no-cache-dir python-multipart || pip install --target /app/.venv/lib/python3.12/site-packages python-multipart
RUN uv pip install --no-cache-dir fastembed python-telegram-bot

FROM python:3.12-slim AS runtime
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/legacy/src:/app \
    PATH="/app/.venv/bin:/usr/local/bin:$PATH"

# Git (for provider clone + DSH) + Node.js 22 (DSH harness requires ^22.19)
# + pnpm (DSH workspaces) + build tools + redis-tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates bsdextrautils git redis-tools && \
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install -y nodejs && \
    npm install -g pnpm@11 && \
    rm -rf /var/lib/apt/lists/*
RUN npm install -g acorn acorn-walk command-code

RUN useradd --create-home --uid 1000 ecms
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY backend/ecms ./ecms
COPY backend/config ./config
COPY backend/alembic.ini ./alembic.ini

# DeepSeek Harness (AegisOS fork): the DSH agent hierarchy spawns
# `node --import tsx/esm apps/cli/src/bin.ts --profile sdk` from this checkout.
# Prebuilt artifacts (lib/) are baked in to avoid OOM in low-RAM build containers.
COPY dsh-full.tgz /tmp/
RUN mkdir -p /app/DSH && tar -xzf /tmp/dsh-full.tgz -C /app/DSH && rm /tmp/dsh-full.tgz
RUN chown -R ecms:ecms /app/DSH

# Legacy providers — Git, MySQL, Jira connectors + pipeline + memory
# --no-deps: all legacy runtime deps already covered by main backend (pymysql,
# fastapi, pydantic, etc.). graphiti-core is optional (raw keyword mode).
RUN pip install --no-cache-dir python-multipart
COPY legacy/src/legacy_ecms ./legacy/src/legacy_ecms
COPY legacy/pyproject.toml ./legacy/pyproject.toml
RUN pip install --no-cache-dir -e /app/legacy --no-deps

ENV NODE_PATH=/usr/lib/node_modules
RUN mkdir -p /workspace /app/data/repos /app/data/mem0_qdrant /app/data/mem0_home /app/memory && \
    chown -R ecms:ecms /workspace /app/data /app/memory

# Entrypoint: runs migrations then starts the server
COPY scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Fix .commandcode ownership: npm -g creates it as root during build
RUN rm -rf /home/ecms/.commandcode && \
    mkdir -p /home/ecms/.commandcode && \
    chown ecms:ecms /home/ecms/.commandcode

# Bundle deployment files into the image for easy extraction
# Usage: docker run --rm brajesh07/ecms-backend:latest cat /deploy/docker-compose.prod.yml > docker-compose.yml
COPY docker/docker-compose.prod.yml /deploy/docker-compose.prod.yml
COPY docker/prometheus /deploy/prometheus
COPY docker/loki /deploy/loki
COPY docker/tempo /deploy/tempo
COPY docker/grafana /deploy/grafana

USER ecms
ENV ECMS_CLI_BINARY=command-code \
    ECMS_WORKSPACE_DIR=/workspace \
    DSH_REPO=/app/DSH \
    AEGISOS_API_URL=http://127.0.0.1:8000
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health').status==200 else 1)"
ENTRYPOINT ["/entrypoint.sh"]

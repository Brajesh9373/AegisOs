#!/bin/bash
# Start the whole AegisOS system (backend + BFF + web + infra).
#
#   ./scripts/start-aegisos.sh          Start all services (builds DSH bundle first if missing)
#   ./scripts/start-aegisos.sh --build  Force rebuild of the DSH bundle + all images
#   ./scripts/start-aegisos.sh --down   Stop all services
#   ./scripts/start-aegisos.sh --logs   Follow logs of all services
#
# The DSH agent hierarchy needs the harness prebuilt (tsc needs ~4GB heap,
# more than low-RAM docker builders have), so compilation happens on the
# host and the backend image just extracts the tarball. No secrets are
# committed: agent LLM keys come from the environment (see below).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARBALL="$ROOT/docker/dsh-full.tgz"
BACKEND_COMPOSE="$ROOT/docker/docker-compose.yml"
FRONTEND_COMPOSE="$ROOT/frontend/docker-compose.yml"
ENV_FILE="$ROOT/.env"
# Pin the Docker context: a stray/broken `default` context (no daemon socket)
# produces "client for node default not found" on build. Override per-machine
# with DOCKER_CONTEXT=... in the environment.
DOCKER="docker --context ${DOCKER_CONTEXT:-desktop-linux}"

# Secrets for the agent hierarchy (export before running, or place in .env):
#   ANTHROPIC_API_KEY / ANTHROPIC_BASE_URL — LLM route for DSH agent sessions
#   ECMS_SERVICE_TOKEN — must match on backend and BFF (BFF→ECMS trust)
#   AEGISOS_API_URL — backend URL the DSH memory tools call (defaults to localhost:8000)

usage() {
  sed -n '2,10p' "$0"
  exit 0
}

check_prereqs() {
  local missing=0
  command -v docker >/dev/null || { echo "missing: docker"; missing=1; }
  if command -v node >/dev/null; then
    local major
    major="$(node -p 'process.versions.node.split(".")[0]')"
    [ "$major" -ge 22 ] || { echo "node >= 22 required (found $major)"; missing=1; }
  else
    echo "missing: node >= 22 (DSH host build)"
    missing=1
  fi
  command -v pnpm >/dev/null || { echo "missing: pnpm (DSH host build)"; missing=1; }
  local mem_gb
  mem_gb="$(free -g | awk '/^Mem:/ {print $2}')"
  if [ "$mem_gb" -lt 6 ]; then
    echo "warning: only ${mem_gb}GB RAM — DSH host build wants 6GB+ (set NODE_OPTIONS to constrain heap)"
  fi
  [ "$missing" -eq 0 ] || exit 1
}

build_dsh_bundle() {
  echo "=== Building DSH bundle on host ==="
  (
    cd "$ROOT/DSH"
    pnpm install
    NODE_OPTIONS=--max-old-space-size=4000 ./node_modules/typescript/bin/tsc -b tsconfig.host.json
    ./node_modules/.bin/tsdown --env.DSH_BUILD_FACE host
  )
  echo "=== Packing $TARBALL ==="
  tar -czf "$TARBALL" --exclude=.git --exclude='node_modules/.cache' -C "$ROOT/DSH" .
  ls -lh "$TARBALL"
}

build_backend() {
  echo "=== Building backend image (embeds $TARBALL) ==="
  $DOCKER compose --env-file "$ENV_FILE" -f "$BACKEND_COMPOSE" build backend
}

build_frontend() {
  echo "=== Building frontend images ==="
  $DOCKER compose --env-file "$ENV_FILE" -f "$FRONTEND_COMPOSE" build api web
}

start_all() {
  echo "=== Starting backend stack ==="
  $DOCKER compose --env-file "$ENV_FILE" -f "$BACKEND_COMPOSE" up -d
  echo "=== Starting frontend stack ==="
  $DOCKER compose --env-file "$ENV_FILE" -f "$FRONTEND_COMPOSE" up -d
}

# Secrets live in .env (gitignored), shared by both stacks so the two
# ECMS_SERVICE_TOKEN values always match. Creates it from .env.example on
# first run, generating a service token when absent.
ensure_env() {
  if [ ! -f "$ENV_FILE" ]; then
    echo "Creating $ENV_FILE from .env.example — fill in ANTHROPIC_API_KEY."
    cp "$ROOT/.env.example" "$ENV_FILE"
  fi
  if ! grep -qE '^ECMS_SERVICE_TOKEN=.{8,}' "$ENV_FILE"; then
    local token
    token="$(openssl rand -hex 32 2>/dev/null || python3 -c 'import secrets;print(secrets.token_hex(32))')"
    if grep -q '^ECMS_SERVICE_TOKEN=' "$ENV_FILE"; then
      sed -i "s|^ECMS_SERVICE_TOKEN=.*|ECMS_SERVICE_TOKEN=$token|" "$ENV_FILE"
    else
      echo "ECMS_SERVICE_TOKEN=$token" >> "$ENV_FILE"
    fi
    echo "Generated ECMS_SERVICE_TOKEN in .env (shared by both stacks)."
  fi
  # shellcheck disable=SC1090
  set -a; . "$ENV_FILE"; set +a
  if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
    echo "NOTE: ANTHROPIC_API_KEY is unset — the platform runs, but DSH agent spawning will fail loud."
  fi
}

wait_healthy() {  echo "=== Waiting for health ==="
  for url in "http://localhost:8000/health:backend" "http://localhost:3001/api/health:BFF" "http://localhost:5173:web"; do
    name="${url##*:}"
    url="${url%:*}"
    for _ in $(seq 1 30); do
      if curl -sf -m 5 "$url" >/dev/null 2>&1; then
        echo "$name: healthy ($url)"
        break
      fi
      sleep 5
    done
  done
  echo
  echo "Backend:  http://localhost:8000  (docs: http://localhost:8000/docs)"
  echo "Frontend: http://localhost:5173"
  if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
    echo "NOTE: ANTHROPIC_API_KEY is unset — DSH agent spawning will fail loud until it is exported."
  fi
}

case "${1:-}" in
  --help|-h) usage ;;
  --down)
    $DOCKER compose --env-file "$ENV_FILE" -f "$FRONTEND_COMPOSE" down
    $DOCKER compose --env-file "$ENV_FILE" -f "$BACKEND_COMPOSE" down
    ;;
  --logs)
    $DOCKER compose --env-file "$ENV_FILE" -f "$BACKEND_COMPOSE" logs -f --tail=100
    ;;
  --build)
    check_prereqs
    ensure_env
    build_dsh_bundle
    build_backend
    build_frontend
    start_all
    wait_healthy
    ;;
  "")
    check_prereqs
    ensure_env
    if [ ! -f "$TARBALL" ]; then
      build_dsh_bundle
    else
      echo "Reusing $TARBALL (use --build to force a rebuild)"
    fi
    # Backend image embeds the tarball; (re)build it whenever we get here.
    build_backend
    build_frontend
    start_all
    wait_healthy
    ;;
  *) echo "unknown flag: $1"; usage ;;
esac

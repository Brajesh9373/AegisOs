#!/bin/bash
# AegisOS Platform Startup Script
# =================================
# Handles DSH bundle preparation, Docker image building, and service startup.
#
# Usage:
#   ./scripts/start-aegisos.sh              # Start all services
#   ./scripts/start-aegisos.sh --build      # Force rebuild DSH bundle + images
#   ./scripts/start-aegisos.sh --dsh-only   # Only rebuild DSH bundle
#   ./scripts/start-aegisos.sh --down       # Stop all services
#   ./scripts/start-aegisos.sh --logs       # Show logs

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DSH_DIR="$PROJECT_ROOT/DSH"
DOCKER_DIR="$PROJECT_ROOT/docker"
DSH_BUNDLE="$PROJECT_ROOT/dsh-full.tgz"
COMPOSE_FILE="$DOCKER_DIR/docker-compose.yml"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() { echo -e "${GREEN}[AegisOS]${NC} $1"; }
warn() { echo -e "${YELLOW}[AegisOS]${NC} $1"; }
error() { echo -e "${RED}[AegisOS]${NC} $1"; }
info() { echo -e "${BLUE}[AegisOS]${NC} $1"; }

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."

    local missing=()

    if ! command -v docker &> /dev/null; then
        missing+=("docker")
    fi

    if ! command -v node &> /dev/null; then
        missing+=("node")
    fi

    if ! command -v pnpm &> /dev/null; then
        missing+=("pnpm")
    fi

    if [ ${#missing[@]} -ne 0 ]; then
        error "Missing prerequisites: ${missing[*]}"
        echo "Please install them before running this script."
        exit 1
    fi

    # Check Node version (requires 22+)
    local node_version=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$node_version" -lt 22 ]; then
        error "Node.js 22+ required. Found: $(node --version)"
        exit 1
    fi

    # Check available memory (DSH build needs ~4GB)
    local available_mem_kb=$(grep MemAvailable /proc/meminfo | awk '{print $2}')
    local available_mem_gb=$((available_mem_kb / 1024 / 1024))
    if [ "$available_mem_gb" -lt 3 ]; then
        warn "Less than 3GB RAM available. DSH build may fail."
        warn "Consider adding swap space or building on a machine with more RAM."
    fi

    log "Prerequisites OK"
}

# Build DSH bundle
build_dsh_bundle() {
    log "Building DSH bundle..."

    if [ ! -d "$DSH_DIR" ]; then
        error "DSH directory not found at $DSH_DIR"
        exit 1
    fi

    cd "$DSH_DIR"

    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        log "Installing DSH dependencies..."
        pnpm install
    fi

    # Generate tsconfig paths
    log "Generating tsconfig paths..."
    NODE_OPTIONS=--max-old-space-size=4000 ./node_modules/.bin/tsx scripts/gen-tsconfig-paths.ts

    # Build TypeScript
    log "Compiling DSH TypeScript..."
    NODE_OPTIONS=--max-old-space-size=4000 ./node_modules/.bin/tsc -b tsconfig.host.json

    # Build host bundles
    log "Building DSH host bundles..."
    ./node_modules/.bin/tsdown --env.DSH_BUILD_FACE host

    # Create bundle tarball
    log "Creating DSH bundle tarball..."
    cd "$PROJECT_ROOT"
    tar -czf "$DSH_BUNDLE" --exclude=.git --exclude='node_modules/.cache' -C DSH .

    local bundle_size=$(du -h "$DSH_BUNDLE" | cut -f1)
    log "DSH bundle created: $DSH_BUNDLE ($bundle_size)"
}

# Build Docker images
build_images() {
    log "Building Docker images..."

    cd "$PROJECT_ROOT"

    # Ensure DSH bundle exists
    if [ ! -f "$DSH_BUNDLE" ]; then
        warn "DSH bundle not found. Building..."
        build_dsh_bundle
    fi

    # Build backend image
    log "Building backend image..."
    docker build -f "$DOCKER_DIR/backend.Dockerfile" -t ecms-backend:latest "$PROJECT_ROOT"

    log "Docker images built successfully"
}

# Start services
start_services() {
    log "Starting AegisOS services..."

    cd "$PROJECT_ROOT"

    # Export environment variables
    export ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-user_59UthjyP4Vt2CxcqErU3gGvGxgiQiao2m8xVCDYYfomxaevK46w45khorDQjT29tHwpz9MCet3Qzx5cL34XhF74R}"
    export ANTHROPIC_BASE_URL="${ANTHROPIC_BASE_URL:-http://127.0.0.1:3457/v1}"

    # Start core infrastructure first
    log "Starting infrastructure (postgres, redis, minio)..."
    docker compose -f "$COMPOSE_FILE" up -d postgres redis minio

    # Wait for postgres
    log "Waiting for postgres..."
    until docker exec ecms-postgres-1 pg_isready -U ecms &> /dev/null; do
        sleep 2
    done

    # Start backend
    log "Starting backend..."
    docker compose -f "$COMPOSE_FILE" up -d backend

    # Wait for backend health
    log "Waiting for backend to be healthy..."
    until curl -s http://localhost:8000/health &> /dev/null; do
        sleep 3
    done

    # Start frontend
    log "Starting frontend..."
    docker compose -f "$COMPOSE_FILE" up -d frontend

    log ""
    log "=================================="
    log "  AegisOS is ready!"
    log "=================================="
    info "  Backend:  http://localhost:8000"
    info "  Frontend: http://localhost:3000"
    info "  Health:   http://localhost:8000/health"
    log ""
    info "  Agent profiles seeded:"
    info "    - head-of-engineering"
    info "    - senior-frontend-engineer"
    info "    - senior-backend-engineer"
    log ""
    info "  LLM Provider: anthropic"
    info "  LLM Model: meituan/LongCat-2.0:free"
    log "=================================="
}

# Stop services
stop_services() {
    log "Stopping AegisOS services..."
    cd "$PROJECT_ROOT"
    docker compose -f "$COMPOSE_FILE" down
    log "Services stopped"
}

# Show logs
show_logs() {
    cd "$PROJECT_ROOT"
    docker compose -f "$COMPOSE_FILE" logs -f --tail=100
}

# Main
main() {
    echo ""
    log "AegisOS Platform Startup"
    echo ""

    case "${1:-}" in
        --build)
            check_prerequisites
            build_dsh_bundle
            build_images
            start_services
            ;;
        --dsh-only)
            check_prerequisites
            build_dsh_bundle
            ;;
        --images-only)
            check_prerequisites
            build_images
            ;;
        --down)
            stop_services
            ;;
        --logs)
            show_logs
            ;;
        --help|-h)
            echo "Usage: $0 [OPTION]"
            echo ""
            echo "Options:"
            echo "  (none)        Start all services (skip build if images exist)"
            echo "  --build       Force rebuild DSH bundle + Docker images, then start"
            echo "  --dsh-only    Only rebuild the DSH bundle tarball"
            echo "  --images-only Only rebuild Docker images (uses existing bundle)"
            echo "  --down        Stop all services"
            echo "  --logs        Show service logs"
            echo "  --help        Show this help message"
            echo ""
            echo "Environment Variables:"
            echo "  ANTHROPIC_API_KEY     Anthropic API key (or compatible proxy)"
            echo "  ANTHROPIC_BASE_URL    Anthropic API base URL"
            echo ""
            echo "Examples:"
            echo "  $0                    # Quick start (uses cached images)"
            echo "  $0 --build            # Full rebuild and start"
            echo "  ANTHROPIC_API_KEY=xxx ANTHROPIC_BASE_URL=http://proxy:80 $0"
            ;;
        *)
            check_prerequisites
            # Check if images exist
            if ! docker image inspect ecms-backend:latest &> /dev/null; then
                log "Backend image not found. Building..."
                build_dsh_bundle
                build_images
            fi
            start_services
            ;;
    esac
}

main "$@"

#!/bin/bash
set -e

ECMS_DIR="/home/ubuntu/ecms"
LOG_FILE="/home/ubuntu/ecms/logs/deploy.log"
LOCK_FILE="/home/ubuntu/ecms/.deploy.lock"
GITHUB_TOKEN="${GITHUB_TOKEN:-}"

mkdir -p "$(dirname "$LOG_FILE")"

# Configure git to use token if available
if [ -n "$GITHUB_TOKEN" ]; then
    cd "$ECMS_DIR"
    git remote set-url origin "https://$GITHUB_TOKEN@github.com/Brajesh9373/ecms.git"
fi

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Prevent concurrent deployments
if [ -f "$LOCK_FILE" ]; then
    log "Deploy already in progress (lock file exists)"
    exit 0
fi

trap 'rm -f "$LOCK_FILE"' EXIT
touch "$LOCK_FILE"

log "Starting deployment..."

cd "$ECMS_DIR"

# Pull latest changes
log "Pulling latest changes..."
git fetch origin main
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" = "$REMOTE" ]; then
    log "Already up to date. Skipping deployment."
    exit 0
fi

git pull origin main
CHANGED_FILES=$(git diff --name-only "$LOCAL" "$REMOTE")
log "Changed files: $CHANGED_FILES"

# Determine what to redeploy
REBUILD_BACKEND=false
REBUILD_FRONTEND=false
RUN_MIGRATIONS=false

while IFS= read -r file; do
    case "$file" in
        backend/*)
            REBUILD_BACKEND=true
            RUN_MIGRATIONS=true
            ;;
        frontend/*)
            REBUILD_FRONTEND=true
            ;;
        docker/*|scripts/*)
            REBUILD_BACKEND=true
            REBUILD_FRONTEND=true
            RUN_MIGRATIONS=true
            ;;
    esac
done <<< "$CHANGED_FILES"

# Run migrations if needed
if [ "$RUN_MIGRATIONS" = true ]; then
    log "Running database migrations..."
    sudo docker compose -f $ECMS_DIR/docker/docker-compose.yml exec -T backend alembic upgrade head 2>&1 | tee -a "$LOG_FILE" || true
fi

# Rebuild and redeploy backend
if [ "$REBUILD_BACKEND" = true ]; then
    log "Rebuilding backend..."
    sudo docker compose -f $ECMS_DIR/docker/docker-compose.yml up -d --build --no-deps backend 2>&1 | tee -a "$LOG_FILE"
    sleep 5
fi

# Rebuild and redeploy frontend
if [ "$REBUILD_FRONTEND" = true ]; then
    log "Rebuilding frontend..."
    sudo docker compose -f $ECMS_DIR/docker/docker-compose.yml up -d --build --no-deps frontend 2>&1 | tee -a "$LOG_FILE"
fi

# Restart nginx to pick up any config changes
log "Reloading nginx..."
sudo docker compose -f $ECMS_DIR/docker/docker-compose.yml exec -T nginx nginx -s reload 2>&1 | tee -a "$LOG_FILE" || true

log "Deployment complete! Deployed commit: $(git rev-parse --short HEAD)"

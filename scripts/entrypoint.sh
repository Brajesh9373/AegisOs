#!/bin/bash
set -e

if [ "$#" -gt 0 ]; then
  exec "$@"
fi

echo "=== Running database migrations ==="
python -m alembic -c /app/alembic.ini upgrade head

echo "=== Ensuring upload directories ==="
mkdir -p /workspace/uploads && chown ecms:ecms /workspace/uploads 2>/dev/null || true

echo "=== Starting ECMS backend ==="
exec uvicorn ecms.main:app --host 0.0.0.0 --port 8000 --log-level info

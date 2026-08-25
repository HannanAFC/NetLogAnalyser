#!/bin/sh
set -e

echo "Running database migrations..."
uv run alembic upgrade head

if [ "$ENVIRONMENT" = "production" ]; then
  echo "Starting backend (production)..."
  exec uv run fastapi run main.py --host 0.0.0.0 --port "${BACKEND_PORT:-8000}"
else
  echo "Starting backend (development)..."
  exec uv run fastapi dev main.py --host 0.0.0.0 --port "${BACKEND_PORT:-8000}"
fi
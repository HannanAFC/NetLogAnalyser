#!/bin/sh

set -e

if [ "$BUILD_MODE" = "production" ]; then
    echo "Running production environment..."
    uv run alembic upgrade head
    uv run fastapi run main.py --host 0.0.0.0 --port 8000
else
    echo "Running development environment..."
    uv run alembic upgrade head
    uv run fastapi dev main.py --host 0.0.0.0 --port 8000
fi
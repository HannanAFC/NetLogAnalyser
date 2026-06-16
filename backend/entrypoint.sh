#!/bin/sh

set -e

if [ "$BUILD_MODE" = "production" ]; then
    echo "Running production environment..."
    exec uv run fastapi run main.py --host 0.0.0.0 --port 8000
else
    echo "Running development environment..."
    exec uv run fastapi dev main.py --host 0.0.0.0 --port 8000
fi
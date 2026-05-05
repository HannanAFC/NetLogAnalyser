#!/bin/sh

set -e

if [ "$BUILD_MODE" = "production" ]; then
    echo "Running production environment..."
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000
else
    echo "Running development environment..."
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir app
fi
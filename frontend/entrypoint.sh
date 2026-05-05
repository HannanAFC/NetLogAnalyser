#!/bin/sh
set -e

if [ "$BUILD_MODE" = "production" ]; then
  echo "Running production environment..."
  pnpm run build
  pnpm run start
else
  echo "Running development environment..."
  pnpm run dev
fi
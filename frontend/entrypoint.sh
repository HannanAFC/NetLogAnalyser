#!/bin/sh
set -e

if [ "$BUILD_MODE" = "production" ]; then
  echo "Running production environment..."
  pnpm run build
  pnpm run start
else
  echo "Running development environment..."
  # Check if node_modules exists and was created with a different lockfile
  if [ -f /node_modules/.pnpm-lock.yaml ] && ! cmp -s /pnpm-lock.yaml /node_modules/.pnpm-lock.yaml 2>/dev/null; then
    echo "Lockfile mismatch, reinstalling dependencies..."
    rm -rf /node_modules
    pnpm install --no-frozen-lockfile
  fi
  # Run dev with no TTY issues
  pnpm run dev
fi
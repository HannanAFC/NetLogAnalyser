#!/bin/sh
set -e

if [ -f /app/node_modules/.pnpm-lock.yaml ] && ! cmp -s /app/pnpm-lock.yaml /app/node_modules/.pnpm-lock.yaml 2>/dev/null; then
  echo "Lockfile mismatch, reinstalling dependencies..."
  rm -rf /app/node_modules
  pnpm install --no-frozen-lockfile
fi

exec pnpm run dev
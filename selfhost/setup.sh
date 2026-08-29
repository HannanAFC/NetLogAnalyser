#!/usr/bin/env bash
set -euo pipefail

ENV_FILE=".env"
COMPOSE_FILE="docker-compose.selfhost.yml"

# Which image tag to pull. install.sh sets NLA_IMAGE_TAG to the release it
# just downloaded the compose file for; running this script directly
# (cloned repo) defaults to "latest".
IMAGE_TAG="${NLA_IMAGE_TAG:-latest}"

if [ ! -f "$ENV_FILE" ]; then
  echo "No .env found - creating one from .env.example"
  cp .env.example "$ENV_FILE"

  SECRET_KEY=$(openssl rand -hex 32)
  DB_PASSWORD=$(openssl rand -hex 24)

  sed -i.bak "s|^SECRET_KEY=.*|SECRET_KEY=${SECRET_KEY}|" "$ENV_FILE"
  sed -i.bak "s|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=${DB_PASSWORD}|" "$ENV_FILE"
  # Anything still marked __GENERATE__ (the password embedded in DATABASE_URL)
  # gets the same DB password so the two stay in sync.
  sed -i.bak "s|__GENERATE__|${DB_PASSWORD}|g" "$ENV_FILE"
  rm -f "${ENV_FILE}.bak"

  echo ""
  echo "Generated SECRET_KEY and POSTGRES_PASSWORD in .env"
  echo "IMPORTANT: back up this .env file. If it's lost while the postgres_data"
  echo "volume still exists, the backend won't be able to authenticate to its"
  echo "own database."
  echo ""
else
  echo ".env already exists - no secrets regenerated."
fi

# Sync IMAGE_TAG independently of the block above, so rerunning this script
# against a newer release (an existing .env, but a fresh IMAGE_TAG passed in)
# actually pulls the matching images, without ever touching SECRET_KEY or
# POSTGRES_PASSWORD.
if grep -q '^IMAGE_TAG=' "$ENV_FILE"; then
  sed -i.bak "s|^IMAGE_TAG=.*|IMAGE_TAG=${IMAGE_TAG}|" "$ENV_FILE"
  rm -f "${ENV_FILE}.bak"
else
  echo "IMAGE_TAG=${IMAGE_TAG}" >> "$ENV_FILE"
fi

echo "Pulling images (${IMAGE_TAG})..."
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" pull

echo "Starting NetLogAnalyser..."
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d

echo ""
echo "Done. Frontend: http://localhost:$(grep '^FRONTEND_PORT=' "$ENV_FILE" | cut -d= -f2)"
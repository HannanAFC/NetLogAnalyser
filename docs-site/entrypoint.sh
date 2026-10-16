# The API reference pages are generated from the backend's OpenAPI schema, which may not be listening yet
attempts=0
until pnpm run generate:api; do
  attempts=$((attempts + 1))
  if [ "$attempts" -ge 20 ]; then
    echo "Could not generate API pages from $OPENAPI_URL after $attempts attempts"
    if [ "$ENVIRONMENT" = "production" ]; then
      exit 1
    fi
    echo "Continuing with the existing pages (development)"
    break
  fi
  echo "Backend not ready, retrying in 3s ($attempts/20)..."
  sleep 3
done

if [ "$ENVIRONMENT" = "production" ]; then
  echo "Starting documentation site (production)..."
  pnpm run build
  pnpm run start --host
else
  echo "Starting documentation site (development)..."
  pnpm run dev --host
fi

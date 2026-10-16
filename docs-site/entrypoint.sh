if [ "$ENVIRONMENT" = "production" ]; then
  echo "Starting documentation site (production)..."
  pnpm run generate:api
  pnpm run build
  pnpm run start --host
else
  echo "Starting documentation site (development)..."
  pnpm run generate:api
  pnpm run dev --host
fi
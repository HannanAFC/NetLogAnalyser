# NetLogAnalyser Docs

This is a Fumadocs application that hosts the full documentation website for NetLogAnalyser. Opposed to the frontend, this is not a static build, a node server needs to be running in order to serve the search API, dynamic OpenGraph images and SSR.

## Testing
Testing is limited to linting, this is because code should rarely be modified, all documentation is written as `.mdx` files and is parsed by the server, so for documentation purposes, code shouldn't be touched.

## Build notes
In order to create the API reference, the application has to fetch the Open API schema from the backend before build time, it will attempt to retry this 3 times before continuing the build process. The `.mdx` files generated from this process are kept out of version control for now as they are automatically generated files and there are a lot of these files. However, the `meta.json` file is still included as it includes grouping for the pages.

## Landing page screenshots
The screenshots on the landing page are generated from a running dev stack rather than captured by hand.

```bash
docker compose --profile dev up      # from the repo root: backend :8000, frontend :3000
pnpm exec playwright install chromium   # first time only
pnpm generate:screenshots
```

`scripts/generate-screenshots.ts` creates (or reuses) a `demo@example.com` account through the backend API, replaces its API keys, ingests about 6.7K synthetic log entries (`scripts/screenshots/seed.ts`), then captures each page in both the dark and light theme with Playwright into `assets/screenshots/<name>-<theme>.png`. It finishes by running `pnpm optimize:images`. Only the PNG sources in `assets/screenshots/` are committed. The AVIF/WebP/JPEG variants and `manifest.json` in `public/screenshots/` are generated and gitignored: `pnpm dev`, `pnpm build` and `pnpm types:check` rebuild them first through `pre` scripts, so the Docker image and fresh clones need no extra step. Output filenames carry a content hash, so they are served with immutable caching, and unchanged sources are skipped (`pnpm optimize:images --force` re-encodes everything).

- To add a screenshot, add a capture to `generate-screenshots.ts` and a matching `<ScreenshotPicture name="..." />` on the page.
- The backend must let the demo account log in. If `EMAIL_VERIFICATION_ENABLED=true`, either turn it off, or set `ENABLE_TEST_ENDPOINTS=true` and `TEST_ENDPOINT_KEY` on the backend and export the same `TEST_ENDPOINT_KEY` when running the script.
- Override the stack URLs with `SCREENSHOT_FRONTEND_URL` and `SCREENSHOT_BACKEND_URL`. The script refuses any host that isn't local (it creates an account and thousands of fake log entries); set `SCREENSHOT_ALLOW_REMOTE=1` to bypass that deliberately.
- `<ScreenshotPicture name="geomap" />` renders both theme variants and shows the one matching the site's theme.
- Each run adds another batch of traffic to the demo account, so the totals in the dashboard shots creep up. Delete the demo account (Settings → Account) to start from scratch.
- The login endpoint is rate limited (`RATELIMIT_AUTH_TIMES`), so avoid running the script many times in quick succession, it is recommended to raise auth rate limits whilst running the generate script or increase the standby time.

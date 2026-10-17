# NetLogAnalyser Frontend

The React single-page app for NetLogAnalyser: login and registration, the live log feed, log history, analytics charts, the anomalies table, the geo map and the settings pages (account, API keys, data exports).

This README explains how the pieces fit together and how to test them..

# Table of Contents
- [Tech stack](#tech-stack)
- [Running the frontend](#running-the-frontend)
- [How the code is organised](#how-the-code-is-organised)
- [How the main parts work](#how-the-main-parts-work)
    - [Runtime config](#runtime-config)
    - [Authentication](#authentication)
    - [Routing](#routing)
    - [Data fetching](#data-fetching)
    - [Live feed](#live-feed)
    - [Time ranges](#time-ranges)
- [Testing](#testing)
- [Linting and type checking](#linting-and-type-checking)

## Tech stack
React 19, TanStack Router (file-based), TanStack Query, TanStack Form with Zod, TanStack Table, Axios, Tailwind CSS 4, Vite, Vitest with Testing Library and MSW, and pnpm.

## Running the frontend
Development happens in Docker. From the **project root** (not this directory):

```sh
docker compose --profile dev up --build
```

The `frontend` container runs the Vite dev server on `http://localhost:3000`, with `./frontend` bind-mounted so changes hot-reload. It expects the backend at `http://localhost:8000`, which the same command starts. The container's entrypoint reinstalls dependencies if `pnpm-lock.yaml` changed, and `pnpm dev` generates `public/config.js` before starting Vite.

Useful scripts, run with `docker compose exec frontend pnpm <script>`:

| Script | What it does |
|---|---|
| `dev` | Generates `config.js` and starts Vite on port 3000 |
| `generate-routes` | Regenerates `src/routeTree.gen.ts` from the files in `src/routes/` |
| `build` | Production build into `dist/` |
| `build:render` | Production build plus a `config.js` baked from `API_BASE_URL` / `WS_BASE_URL` (used on Render) |
| `preview` | Serves the production build locally |
| `lint` / `format` | ESLint check / ESLint auto-fix |
| `check` | TypeScript type check (`tsc --noEmit`) |
| `test` | Unit tests |
| `test:integration` | Integration tests against a real backend |
| `test:all` | Both |

## How the code is organised
Everything lives under `src/` and is imported through the `#/` alias (`#/features/auth/hooks`, never `../../features/...`).

| Directory | Purpose |
|---|---|
| `routes/` | One file per page. `_authenticated/` is a layout route that guards everything inside it |
| `features/<name>/` | One folder per backend area: `auth`, `api-keys`, `logs`, `live-feed`, `analytics`, `exports`, `users` |
| `lib/` | Shared infrastructure: the Axios client, env access, token store, time-range helpers, the overlay (modal) system and shared types |
| `components/` | UI components, grouped by page area, with design-system primitives in `components/ui/` |

Each feature folder follows the same four-file pattern, and data flows down this chain:

```
api.ts  ->  queries.ts  ->  hooks.ts  ->  components
 HTTP        query options    hooks         only ever import hooks
```

`schemas.ts` holds the Zod schemas that validate forms and mirror the backend's validation. Components import from a feature's `hooks.ts` only, never from `api.ts` or `queries.ts`.

## How the main parts work

### Runtime config
The app does not use build-time `VITE_*` variables for URLs. `index.html` loads `/config.js`, which sets `window.__ENV__`, and the rest of the code reads it through `#/lib/env`. That is what lets a single self-host image run on any host.

- **Local dev and Render:** `scripts/generate-config.mjs` writes `config.js` from `API_BASE_URL`, `WS_BASE_URL` and `APP_VERSION`.
- **Self-host:** `entrypoint.selfhost.sh` runs `envsubst` over `config.js.template` at container start. If `BACKEND_PORT` is set, URLs are derived from `location.hostname`.

### Authentication
The access token (a JWT) lives **in memory only** in `lib/auth/token-store.ts`, never in `localStorage`. The refresh token is an httpOnly cookie that JavaScript cannot read; Axios sends it with `withCredentials`.

On page load, the session query sees there is no access token, calls `/auth/refresh` and then `/users/me`. If any request gets a `401`, the Axios interceptor in `lib/api/client.ts` refreshes once (shared across concurrent requests) and retries. If that fails, the session cache is set to `null` and the `_authenticated` layout redirects to `/login`.

### Routing
TanStack Router builds the route tree from the files in `src/routes/`. After adding, moving or deleting a route file, run `pnpm generate-routes`, or TypeScript will complain about missing route types. Search params (such as the time range) are validated with Zod via `validateSearch`.

### Data fetching
All HTTP goes through the shared `apiClient`. TanStack Query defaults are in `lib/api/query-client.ts` (30 s `staleTime`, no refetch on window focus). Query options are defined once in `queries.ts` and reused by both route loaders and hooks, so a query key is never duplicated. Use `apiError()` from `lib/api/errors.ts` to turn an Axios error into a readable message.

### Live feed
`features/live-feed/connection.ts` contains `LiveFeedSocket`. It requests a one-time ticket over HTTP, opens `ws://.../ws/live?ticket=...`, sends a heartbeat every 25 seconds and reconnects with exponential backoff. Every message is validated with Zod before it reaches React state. `useLiveFeed` combines the socket with the most recent logs fetched over HTTP and keeps at most 200 entries.

### Time ranges
The analytics pages share a time-range picker backed by URL search params (`lib/time-range/`). `resolveTimeRange()` turns a preset or custom range into `{ start, end }`, clamped to the backend's 30-day maximum, and the bucket helpers pick minute, hour or day buckets so a chart never exceeds 1,000 points.

## Testing
There are two kinds of test, both run with Vitest (`vitest.config.ts` defines them as separate projects).

### Unit tests
Unit tests sit next to the code as `*.test.ts(x)` files under `src/`. They run in jsdom, **need no backend**, and mock the network with MSW. Run them in the frontend container from the project root:

```sh
# All unit tests
docker compose exec frontend pnpm test

# One file
docker compose exec frontend pnpm vitest run --project unit src/features/auth/schemas.test.ts

# Tests whose name matches a pattern
docker compose exec frontend pnpm vitest run --project unit -t "refresh"

# Watch mode while developing
docker compose exec frontend pnpm vitest --project unit
```

How the setup works:
- `test/setup.ts` sets `window.__ENV__`, starts the MSW server (`onUnhandledRequest: 'error'`, so a request without a handler fails the test) and resets mock state after each test.
- `test/mocks/handlers.ts` holds the default MSW handlers. Override them inside a test with `server.use(...)` when you need a different response; they are reset afterwards.
- `test/test-utils.tsx` has render helpers with the providers components need.

### Integration tests
The files in `test/integration/*.real-backend.test.ts` call a **real running backend** over HTTP: register, verify email, log in, manage API keys. They only run when `RUN_INTEGRATION_TESTS=1`, which `pnpm test:integration` sets for you, and are skipped otherwise.

They need the backend to be started in test mode:
- `ENABLE_TEST_ENDPOINTS=true` and a `TEST_ENDPOINT_KEY`, so the tests can fetch verification and reset tokens from `/test-only/last-token` instead of reading an email.
- `EMAIL_VERIFICATION_ENABLED=true`, as in CI.
- Rate limits raised high enough that a full run isn't throttled (the `RATELIMIT_*` variables; CI uses `10000000`).

The tests read `API_BASE_URL` (default `http://localhost:8000`) and `TEST_ENDPOINT_KEY` from the environment. The integration tests create real users, so point the backend at the test database, not your dev database.

```sh
# From the host, with the stack running and the backend in test mode (port 8000 is published)
cd frontend
TEST_ENDPOINT_KEY=A-TESTING-KEY pnpm test:integration

# Everything
TEST_ENDPOINT_KEY=A-TESTING-KEY pnpm test:all
```

Running them from the host needs `pnpm install` once in this directory. To run them inside the container instead, also pass `-e API_BASE_URL=http://backend:8000`, because `localhost` inside the container is not the backend.

CI (`.github/workflows/tests.yml`) starts Postgres and Redis, migrates and starts the backend with the settings above, then runs `pnpm run test:all` and `pnpm run lint`.

When you add a feature, write tests for its schemas, query and hook behaviour (using MSW) and for any non-trivial component. Existing `*.test.ts` files beside `schemas.ts`, `queries.ts` and `hooks.ts` are good examples.

## Linting and type checking
Formatting is enforced by ESLint with `@stylistic` (there is no Prettier): tabs, single quotes, semicolons, no trailing commas, and spaces inside parentheses, brackets and braces.

```sh
docker compose exec frontend pnpm lint     # check
docker compose exec frontend pnpm format   # auto-fix
docker compose exec frontend pnpm check    # tsc --noEmit
```

Before finishing a change, `pnpm lint`, `pnpm check` and `pnpm test` must all pass with no new errors. CI also runs lint with `--max-warnings=0`.

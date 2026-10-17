# NetLogAnalyser Backend

The FastAPI service behind NetLogAnalyser. It authenticates users, ingests network logs sent with an API key, enriches them with geo and anomaly information, stores them in Postgres and streams them live to the dashboard over a WebSocket. A separate Arq worker runs the slow jobs (data exports and account deletion), and a retention job cleans up old data.

This README explains how the pieces fit together and how to test them.

# Table of Contents
- [Tech stack](#tech-stack)
- [Running the backend](#running-the-backend)
- [How the code is organised](#how-the-code-is-organised)
- [How the main parts work](#how-the-main-parts-work)
    - [Authentication](#authentication)
    - [Ingest](#ingest)
    - [Live feed](#live-feed)
    - [Logs and analytics](#logs-and-analytics)
    - [Exports and the worker](#exports-and-the-worker)
    - [Data retention](#data-retention)
- [Database and migrations](#database-and-migrations)
- [Testing](#testing)
- [Linting](#linting)

## Tech stack
FastAPI, SQLAlchemy 2.0 (async) with Postgres, Redis (rate limiting, Pub/Sub, locks, caching, job queue), Arq for background jobs, Alembic for migrations, MaxMind GeoLite2 for IP geolocation, `uv` for dependency management. Python 3.14. *Python 3.15 introduces breaking changes to event loops, so it is not a planned upgrade for now.*

## Running the backend
The backend is developed inside Docker so Python and its dependencies are independent of your machine. From the **project root** (not this directory):

```sh
docker compose --profile dev up --build
```

This starts the API on `http://localhost:8000` (with auto-reload, as `./backend` is bind-mounted), the `export-worker`, Redis, Postgres (`db`), the test database (`test-db`) and the frontend. On start, the container runs `alembic upgrade head` and then `fastapi dev`. Check it with `GET http://localhost:8000/health`, and browse the interactive API docs at `http://localhost:8000/docs`.

All configuration comes from the `.env` file in the project root, copied from `.env.example`. It is read through the `settings` singleton in `config.py`; never read environment variables directly.

## How the code is organised
Each feature is a package with the same layout for consistency and easy of development:

| File | Responsibility |
|---|---|
| `router.py` | HTTP concerns only: parse the request, call the service, build the response |
| `service.py` | Business logic. Takes `db: AsyncSession` as a parameter and can be tested without HTTP |
| `schemas.py` | Pydantic request and response models |
| `dependencies.py` | FastAPI dependencies (where the feature needs them) |

| Package | What it does |
|---|---|
| `auth/` | Register, login, refresh, logout, password reset, email verification. Hashing and token helpers live in `security.py` |
| `users/` | `/users/me`: profile, password change, account deletion |
| `api_keys/` | Create, list and revoke API keys; `verify_api_key` for `/ingest` |
| `ingest/` | `POST /ingest`, geo enrichment and anomaly scoring (`anomaly.py`) |
| `logs/` | `GET /logs`, cursor-paginated history |
| `analytics/` | `GET /analytics/*`: summary, timeseries, top talkers, protocols, geo, anomalies |
| `websocket/` | Ticket endpoint, `/ws/live`, the in-process connection manager and Redis Pub/Sub listener |
| `exports/` | Create/list exports, download links, CSV/JSONL formatting, local and S3 storage |
| `retention/` | `python -m retention.job`: warn, delete and purge-exports modes |
| `worker/` | Arq worker settings and the API-side job pool |
| `email_service/` | Resend client, templates and sending helpers |
| `cache/`, `rate_limiter/`, `geoip/` | Shared Redis pool, rate-limit tiers, MaxMind lookups |
| `models/models.py` | Every SQLAlchemy model (all 7 tables) |
| `testing/` | Test-only endpoints, enabled by `ENABLE_TEST_ENDPOINTS` (used by the frontend integration tests) |
| `alembic/` | Migrations |
| `tests/` | The pytest suite |

`main.py` builds the app, registers the routers and middleware, and opens and closes the Redis pool, Arq pool and Pub/Sub listener in its lifespan.

## How the main parts work

### Authentication
- Access tokens are short-lived JWTs, sent in the `Authorization` header and checked on every request by the `get_current_user` dependency.
- Refresh tokens are random values stored only as SHA-256 hashes in Postgres and sent in an httpOnly cookie. Each login gets a `family_id`; if a revoked token is ever reused, the whole family is revoked.
- Passwords use Argon2id (`hash_password`), while tokens and API keys use SHA-256 (`hash_token`). Always go through `auth/security.py`.

### Ingest
`POST /ingest` takes a batch of entries and an `X-API-Key` header. The key is looked up in a Redis cache first and the database second. Each entry is validated individually, enriched (country for source and destination IPs, anomaly score from `ingest/anomaly.py`) and inserted in bulk, falling back to row-by-row inserts if the bulk insert fails. The response is always `207`, listing which entries were rejected and why; one bad entry never rejects the batch. Accepted rows are then published to Redis for the live feed.

### Live feed
The browser first calls `POST /ws/ticket` with its JWT and gets a single-use ticket that expires after 30 seconds. It then opens `/ws/live?ticket=...`, which passes a rate limit, an origin check, the ticket check and a per-user connection limit before it is accepted. Ingest publishes to a Redis Pub/Sub channel; every API process runs a listener that forwards messages to the sockets it owns through the `ConnectionManager`. Only allowlisted fields are broadcast.

### Logs and analytics
`GET /logs` pages over `(captured_at, id)` with opaque base64 cursors, newest first. `GET /analytics/*` aggregates the same table over a time range (30 days at most). Summary and timeseries responses are cached in Redis for a short time. Every query is filtered by the `user_id` from the JWT.

### Exports and the worker
`POST /exports` records a `PENDING` row, enqueues a job and returns `202`. The Arq worker (`export-worker`, running `arq worker.settings.WorkerSettings`) streams the user's logs into a zip of `logs.csv` and `logs.jsonl`, stores it locally or in S3, and marks the row `READY`. Downloads go through short-lived, hashed tokens held in Redis. Account deletion also runs on the worker. The API and worker must share the export volume when using local storage (compose does this).

### Data retention
Retention runs outside the API, in three modes. `warn` exports a user's expiring logs and emails them a link, `delete` removes expired logs only for users who were successfully warned, and `purge-exports` removes expired export files. Each mode takes a Redis lock so runs never overlap.

```sh
docker compose exec backend python -m retention.job --mode warn
docker compose exec backend python -m retention.job --mode delete
docker compose exec backend python -m retention.job --mode purge-exports
```

## Database and migrations
Models live in `models/models.py` and use SQLAlchemy 2.0 style (`Mapped` and `mapped_column`). Never edit a migration that has already been applied; write a new one instead.

```sh
# After changing models/models.py
docker compose exec backend alembic revision --autogenerate -m "describe the change"

# Read the generated file before applying it, autogenerate is not always right
docker compose exec backend alembic upgrade head

# Roll back one step
docker compose exec backend alembic downgrade -1
```

The backend container runs `alembic upgrade head` on every start.

## Testing
The tests are pytest tests that run against a real Postgres and a real Redis. Because the services only resolve each other's hostnames inside the compose network, **run the tests inside the backend container**, from the project root, with the stack running (`docker compose --profile dev up`).

```sh
# The whole suite
docker compose exec -e DATABASE_URL="postgresql+psycopg://NetlogAnalyserUserTest:TestPass@test-db/NetLogAnalyserDBTest" backend pytest -v

# One file
docker compose exec -e DATABASE_URL="postgresql+psycopg://NetlogAnalyserUserTest:TestPass@test-db/NetLogAnalyserDBTest" backend pytest tests/test_auth.py -v

# One test, matched by name
docker compose exec -e DATABASE_URL="postgresql+psycopg://NetlogAnalyserUserTest:TestPass@test-db/NetLogAnalyserDBTest" backend pytest tests/test_auth.py -k "login" -v
```

`docker exec -it <container> pytest ...` also works if you prefer attaching to a container by name; check the name with `docker ps`.

**Always point `DATABASE_URL` at `test-db`**, as in the commands above. The container's `.env` points `DATABASE_URL` at your development database, and `tests/conftest.py` only falls back to the test database when the variable is unset. The suite creates all tables at the start and drops them at the end, so running it against the dev database would destroy your data.

**The tests flush Redis.** The `redis_client` fixture runs `FLUSHDB` on `REDIS_URL` before and after each test that uses it. In the dev stack this is the same Redis the running app uses, so cached analytics, pending WebSocket tickets, connection slots and rate-limit counters are wiped while the suite runs.

How the suite is set up (`tests/conftest.py`):
- **Database isolation.** Each test runs inside a transaction that is rolled back afterwards, so tests don't leak rows into each other.
- **`client` fixture.** An `httpx.AsyncClient` over `ASGITransport` with `get_db` and the rate limiters overridden. The lifespan is *not* run, so anything needing it (Redis pool, Arq pool) is set up or mocked by the fixtures.
- **Async tests.** Mark them with `@pytest.mark.anyio`.
- **Rate limits.** Override the `get_*_rate_limiter` dependencies via `app.dependency_overrides`. For tests of enforcement itself, use `build_strict_limiter(times, seconds)` from `conftest.py`.
- **Test data.** `tests/factories.py` has ORM factories, and `conftest.py` has constants such as `VALID_EMAIL` and `VALID_PASSWORD`.

CI (`.github/workflows/tests.yml`) runs `uv run pytest -v` in this directory against Postgres and Redis service containers.

When you add a feature, add tests in `tests/test_<feature>.py`. Cover the error paths and the security behaviour (user scoping, invalid input, auth failures), not just the happy path.
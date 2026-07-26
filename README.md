# NetLogAnalyser

A real-time network log analysis platform. Users send network packet data to a
REST API using an API key; the data is stored, enriched with geo and anomaly
information, and streamed live to a React dashboard.

---

## Architecture

```
Browser (React SPA)
    │  JWT in Authorization header (in-memory)
    │  Refresh token in httpOnly cookie
    ▼
FastAPI (backend/)
    │  JWT verified on every request
    │  API key verified on /ingest
    │  WebSocket at /ws/live streams new entries to dashboard
    ▼
Postgres (Neon, serverless)
    │  Users, API keys, refresh tokens, log entries
    ▼
Redis
    │  Rate limiting (auth, forgot-password, ingest, general, WebSocket)
    ▼
External
    MaxMind GeoLite2-Country.mmdb  (IP → country_code)
```

| Layer | Technology |
|---|---|
| Backend | FastAPI + SQLAlchemy 2.0 (async) + Alembic |
| Frontend | React 19 + TanStack Router + TanStack Query + Tailwind CSS 4 |
| Database | PostgreSQL (Neon in production, local container in dev) |
| Cache | Redis 7 |
| Auth | JWT access tokens + httpOnly refresh tokens + Argon2id passwords |
| Email | Resend (onboarding, verification, password recovery) |

---

## Running the development environment

### Prerequisites
- Docker Desktop
- A `.env` file at the project root (copy from `.env.example` and fill in values)

### Start all services
```bash
docker compose up --build
```

### Verify everything works
1. `GET http://localhost:8000/health` should return:
`{"database":"ok","version":"...","uptime_seconds":...,"environment":"..."}`
2. Open `http://localhost:3000` - you should see the login page
3. Register an account and confirm you land on the dashboard

### Services

| Service | Port | Container |
|---|---|---|
| Frontend (Vite) | `3000` | `NetLogAnalyser-Frontend` |
| Backend (FastAPI) | `8000` | `NetLogAnalyser-Backend` |
| PostgreSQL | `5432` | `NetLogAnalyser-DB` |
| Test PostgreSQL | `5433` | `NetLogAnalyser-TestDB` |
| Redis | `6379` | `NetLogAnalyser-Redis` |

---

## Running tests

All tests run inside their respective Docker containers.

### Backend tests
```bash
# Attach to the backend container and run pytest
docker exec -it NetLogAnalyser-Backend sh
> DATABASE_URL=postgresql+asyncpg://NetlogAnalyserUserTest:TestPass@test-db:5432/NetLogAnalyserDBTest pytest tests/ -v

# Or as a single command
docker exec -it NetLogAnalyser-Backend sh -c \
  "DATABASE_URL=postgresql+asyncpg://NetlogAnalyserUserTest:TestPass@test-db:5432/NetLogAnalyserDBTest pytest tests/ -v"
```

The test database (`NetLogAnalyser-TestDB`) is a separate container that starts
alongside the main database. Set `DATABASE_URL` to point to it when running tests.

### Frontend checks
```bash
# Attach to the frontend container
docker exec -it NetLogAnalyser-Frontend sh

# Run linting
pnpm lint

# Run type checking
pnpm check
```

### Frontend integration tests
Frontend integration tests run against a real backend. Make sure both the
frontend and backend containers are running, then:

```bash
docker exec -it NetLogAnalyser-Frontend sh
pnpm test
```

---

## Deployment

- **Frontend**: static site on Render.com
- **Backend**: Hetzner VPS via DokPloy
- **Database**: Neon (serverless Postgres)
- **Tunneling**: Cloudflare + cloudflared (via Dokploy)
- **Access control**: Tailscale + Cloudflare Access for the Dokploy dashboard

---

## Key design decisions

- **Argon2id** for passwords, **SHA-256** for tokens/API keys
- **JWT access tokens**  short-lived (30 min), stateless, in-memory on frontend
- **Refresh tokens**  long-lived (30 days), SHA-256 hashed in DB, httpOnly cookie
- **Token family**  reuse of a revoked refresh token revokes the entire family
- **`INET` type** for IP columns  validated at DB level, enables subnet queries
- **`BigInteger`** for `log_entries.id`  sequential performance for the
  highest-row-count table; UUIDs for all other primary keys
- **`captured_at` vs `inserted_at`**  client capture time vs server receipt time
- **Rate limiting**  Redis-backed, separate limiters per endpoint category
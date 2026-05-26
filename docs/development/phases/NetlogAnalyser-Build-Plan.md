# NetLogAnalyser — Build Plan

A phased roadmap for building the NetLogAnalyser real-time network log visualiser.
Each phase has a clear goal, ordered tasks, and the exact skills and libraries
you need to learn to execute it.

---

## How to use this document

Work through the phases in order. Each phase produces something tangible you
can demo or test before moving on. Don't start Phase 3 until Phase 2 is
working end-to-end — the temptation to jump ahead is the most common reason
projects stall.

---

## Phase 1 — Environment & Foundations
**Goal:** Both services (FastAPI backend, React frontend) start locally and
can talk to each other. Postgres is running. No real features yet.

### Tasks
- [ ] Install tooling: Python 3.12+, Node 20+, Docker Desktop
- [ ] Create a `docker-compose.yml` that starts Postgres and pgAdmin
- [ ] Scaffold the FastAPI project using the directory structure from the
      backend plan
- [ ] Connect FastAPI to Postgres using SQLAlchemy async — verify with a
      `/health` endpoint that queries the DB
- [ ] Scaffold the React project: run `npm install`, confirm Vite dev server
      starts and the proxy to FastAPI works
- [ ] Set up Alembic for database migrations — create the initial migration
      with all five tables from the schema

### Skills & libraries to learn

**Python / FastAPI**
- [FastAPI docs — first steps](https://fastapi.tiangolo.com/tutorial/first-steps/)
  Learn how routes, request bodies, and responses work. Focus on the tutorial
  up to "Path Parameters" and "Request Body".
- [Pydantic v2 — models](https://docs.pydantic.dev/latest/concepts/models/)
  Every request and response in FastAPI is validated by a Pydantic model.
  Learn field types, validators, and `model_config`.
- [SQLAlchemy 2.0 async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
  The async session pattern is different from the classic SQLAlchemy you'll
  find in older tutorials. Focus on `AsyncSession`, `async_sessionmaker`, and
  `select()` statements.
- [Alembic — tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
  Learn `alembic init`, `alembic revision --autogenerate`, and
  `alembic upgrade head`. You'll run these commands every time the schema
  changes.

**Docker**
- [Docker Compose — getting started](https://docs.docker.com/compose/gettingstarted/)
  You only need enough to run Postgres + pgAdmin locally. Focus on the
  `services`, `environment`, and `volumes` keys.

**Postgres**
- [PostgreSQL tutorial](https://www.postgresql.org/docs/current/tutorial.html)
  Work through chapters 1–5 (SQL basics). You'll write raw SQL for the
  analytics queries later so understanding `GROUP BY`, `WHERE`, and
  window functions matters.

---

## Phase 2 — Authentication
**Goal:** A user can register, log in, receive a JWT, and log out. The refresh
token flow works. Protected routes reject requests without a valid token.

### Tasks
- [ ] Implement `POST /auth/register` — hash password with bcrypt, insert user
- [ ] Implement `POST /auth/login` — verify password, issue JWT access token,
      set httpOnly refresh token cookie
- [ ] Implement `POST /auth/refresh` — read cookie, issue new access token
- [ ] Implement `POST /auth/logout` — revoke refresh token row in DB
- [ ] Write the `get_current_user` FastAPI dependency using `Depends()`
- [ ] Write the `verify_api_key` dependency for the ingest endpoint
- [ ] Build the React `Login` and `Register` pages
- [ ] Wire `AuthContext` — confirm silent session restore works on page refresh
- [ ] Add the `ProtectedRoute` guard — confirm it redirects unauthenticated
      users to `/login`
- [ ] Test the full cycle: register → login → refresh → logout

### Skills & libraries to learn

**Backend**
- [python-jose — JWT](https://python-jose.readthedocs.io/en/latest/)
  Used for encoding and decoding JWTs. Learn `jwt.encode()`,
  `jwt.decode()`, and how to set `exp` (expiry) claims.
- [passlib — password hashing](https://passlib.readthedocs.io/en/stable/narr/quickstart.html)
  One page of reading. Use `CryptContext` with `bcrypt` scheme. Know
  `hash()` and `verify()`.
- [FastAPI — security / dependencies](https://fastapi.tiangolo.com/tutorial/security/)
  Read the "OAuth2 with Password" section. The `Depends()` pattern for
  injecting the current user into route handlers is the most important
  FastAPI concept to fully understand.
- [FastAPI — cookies](https://fastapi.tiangolo.com/tutorial/cookie-params/)
  You need `Response.set_cookie()` with `httponly=True` and `samesite="lax"`
  for the refresh token.

**Frontend**
- [TanStack Query — mutations](https://tanstack.com/query/latest/docs/framework/react/guides/mutations)
  Login and register are mutations, not queries. Learn `useMutation`,
  `onSuccess`, and `onError`.
- [React Router — navigation](https://reactrouter.com/en/main/hooks/use-navigate)
  Learn `useNavigate` to redirect after a successful login, and
  `Navigate` for the protected route redirect.
- React `useContext` + `createContext` — already implemented in
  `AuthContext.jsx` but read the React docs on context to understand
  why the provider pattern is structured the way it is.

---

## Phase 3 — API Key Management
**Goal:** A logged-in user can create, label, and revoke API keys through the
dashboard. The plaintext key is shown once on creation.

### Tasks
- [ ] Implement `GET /api-keys`, `POST /api-keys`, `PATCH /api-keys/{id}`,
      `DELETE /api-keys/{id}`
- [ ] Key generation: use `secrets.token_hex(32)`, store only the SHA-256
      hash and the first 8-char prefix
- [ ] Build the `ApiKeys` page — key list, create modal, revoke confirmation
- [ ] Show the plaintext key in a one-time reveal banner on creation (matches
      the mockup)
- [ ] Implement the copy-to-clipboard button

### Skills & libraries to learn

**Backend**
- Python `secrets` module — one function: `secrets.token_hex()`. No library
  needed; it's in the standard library.
- Python `hashlib` — `hashlib.sha256(key.encode()).hexdigest()` to hash the
  key before storage.

**Frontend**
- [TanStack Query — invalidation](https://tanstack.com/query/latest/docs/framework/react/guides/invalidations-from-mutations)
  After creating or revoking a key, call
  `queryClient.invalidateQueries({ queryKey: ['api-keys'] })` in
  `onSuccess`. This is the pattern you'll use everywhere mutations change
  server data.
- [Clipboard API](https://developer.mozilla.org/en-US/docs/Web/API/Clipboard/writeText)
  One line: `navigator.clipboard.writeText(value)`. Used for the copy button.
- React controlled inputs and modal state — learn `useState` for the
  "create key" modal open/close and the label input field.

---

## Phase 4 — Log Ingestion
**Goal:** An external client can POST a batch of log entries to `/ingest`
using an API key. Entries are validated, enriched, and persisted to Postgres.

### Tasks
- [ ] Implement `POST /ingest` — authenticate via API key, validate batch
      with Pydantic, bulk-insert to `log_entries`
- [ ] Integrate IP geolocation: look up `country_code` from `src_ip` on
      ingest using a local MaxMind GeoLite2 database (no API call per request)
- [ ] Implement basic anomaly scoring — a simple rules engine is fine:
      - Port scan: same src_ip, >20 different dst_ports in 60 seconds → score 0.9
      - Brute force: same src_ip → dst_port 22 or 3389, >10 attempts in 60s → score 0.88
      - Volume spike: src_ip packet rate >5× its own 5-minute average → score 0.73
      - Unusual port: dst_port not in a known-safe list → score 0.4
- [ ] Write a Python test script that sends realistic synthetic log batches
      so you can populate the DB without real network traffic
- [ ] Update `last_used_at` on the API key row after each successful ingest

### Skills & libraries to learn

**Backend**
- [geoip2 — MaxMind](https://geoip2.readthedocs.io/en/latest/)
  Download the free GeoLite2-Country `.mmdb` file from MaxMind. Use
  `geoip2.database.Reader` to look up a country code from an IP in one line.
  This runs locally with no network call.
- [SQLAlchemy — bulk insert](https://docs.sqlalchemy.org/en/20/orm/queryguide/dml.html)
  Use `session.execute(insert(LogEntry), list_of_dicts)` for bulk ingestion.
  Never insert in a loop — it's 100× slower.
- Pydantic validators — learn `@field_validator` to validate IP address
  format, port ranges (0–65535), and protocol values on ingest.
- Python `collections.deque` — useful for the in-memory sliding window used
  by the anomaly scoring rules (keep a deque of recent timestamps per IP).

**Testing**
- [httpx](https://www.python-httpx.org/) — use this to write the synthetic
  ingest script. It's also what FastAPI's `TestClient` is built on, so
  learning it now pays off when you write proper tests later.

---

## Phase 5 — Log History & Query API
**Goal:** The log history page works — paginated, filterable, with expandable
row detail. The `/logs` endpoint supports all the query params from the design.

### Tasks
- [ ] Implement `GET /logs` with pagination (`page`, `limit`) and filters
      (`from`, `to`, `protocol`, `src_ip`, `country_code`, `anomaly_only`)
- [ ] Implement `GET /logs/{id}` returning the full entry including
      `raw_payload`
- [ ] Implement `DELETE /logs` bulk deletion by time range
- [ ] Build the `LogHistory` page — filter bar, table with sorting, expandable
      rows, pagination controls
- [ ] Add the anomaly score bar component (reusable — you'll use it elsewhere)
- [ ] Sync filter state to the URL query string so links are shareable and
      filters survive a page refresh

### Skills & libraries to learn

**Backend**
- SQLAlchemy dynamic filtering — learn how to conditionally add `.where()`
  clauses to a query based on which params were provided. The pattern is:
  ```python
  stmt = select(LogEntry)
  if protocol:
      stmt = stmt.where(LogEntry.protocol == protocol)
  ```
- SQLAlchemy `func.count()` with `select()` — needed to return the total
  count for pagination alongside the page of results.
- Postgres indexes — add a composite index on `(user_id, captured_at DESC)`
  in an Alembic migration. Run `EXPLAIN ANALYZE` on your query before and
  after to see the difference. Understanding query plans is a good
  dissertation talking point.

**Frontend**
- [TanStack Query — query keys with filters](https://tanstack.com/query/latest/docs/framework/react/guides/query-keys)
  Include the full filter object in the `queryKey` array. TanStack Query
  will automatically refetch when any filter value changes.
- [React Router — search params](https://reactrouter.com/en/main/hooks/use-search-params)
  `useSearchParams` lets you read and write URL query params as state.
  Use it to sync the filter bar — this is a small but impressive detail.
- `usePagination` hook — already written for you. Wire it up and call
  `reset()` whenever a filter changes so you don't land on page 50 of
  a result set that only has 2 pages.

---

## Phase 6 — Analytics Endpoints & Dashboard Charts
**Goal:** All five analytics endpoints are working and the Dashboard page
is fully live with real data — traffic chart, protocol pie, top talkers,
and threat feed.

### Tasks
- [ ] Implement `GET /analytics/traffic` — time-bucketed packet counts using
      Postgres `date_trunc()`
- [ ] Implement `GET /analytics/protocols` — GROUP BY protocol with counts
      and percentages
- [ ] Implement `GET /analytics/geo` — GROUP BY country_code with counts
- [ ] Implement `GET /analytics/top-talkers` — GROUP BY src_ip ORDER BY COUNT
- [ ] Implement `GET /analytics/anomalies` — recent entries above threshold
- [ ] Build the full `Dashboard` page consuming all five endpoints via
      TanStack Query with `refetchInterval`
- [ ] Build the `Analytics` page with a longer time-range selector and
      deeper breakdowns

### Skills & libraries to learn

**Backend**
- [Postgres `date_trunc`](https://www.postgresql.org/docs/current/functions-datetime.html)
  The key function for time-series bucketing. Example:
  `date_trunc('minute', captured_at)` groups timestamps into per-minute
  buckets. Combine with `GROUP BY` to get packet counts per interval.
- SQLAlchemy `func` — wraps Postgres functions:
  `func.date_trunc('minute', LogEntry.captured_at)`. Learn to use it
  alongside `group_by()` and `order_by()`.

**Frontend**
- [Recharts](https://recharts.org/en-US/api)
  The library already in `package.json`. Focus on `LineChart` for traffic,
  `PieChart`/`RadialBarChart` for protocols. Read the "Customization" docs
  — you'll need custom tooltips and tick formatters.
- [TanStack Query — `refetchInterval`](https://tanstack.com/query/latest/docs/framework/react/guides/important-defaults)
  Set `refetchInterval: 5000` on your analytics queries so charts update
  automatically without a WebSocket.

---

## Phase 7 — Real-Time WebSocket
**Goal:** New log entries appear on the Dashboard and live feed page
instantly as they are ingested, without polling.

### Tasks
- [ ] Implement the `ConnectionManager` in `websocket/manager.py` — a dict
      of `user_id → list[WebSocket]` with `connect`, `disconnect`, and
      `broadcast` methods
- [ ] Implement `GET /ws/live` — authenticate via the `?token=` query param,
      register the connection, and push new entries as they arrive
- [ ] Call `manager.broadcast()` from the ingest service after a successful
      bulk insert
- [ ] Wire `useLiveStream` hook (already written) into the Dashboard —
      prepend incoming events to the traffic chart data and threat feed
- [ ] Build the dedicated `LiveFeed` page — a rolling table of the last 200
      entries, newest at the top, updating in real time
- [ ] Handle the WebSocket status indicator in the topbar (the pulsing green
      "Live" badge)

### Skills & libraries to learn

**Backend**
- [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/)
  Read the full page. Focus on the `WebSocket` dependency, `accept()`,
  `send_json()`, and handling `WebSocketDisconnect`.
- Python `asyncio` basics — you don't need to be an expert, but understand
  `async def`, `await`, and why you can't call a sync function inside an
  async route without `run_in_executor`. The FastAPI docs explain this in
  context.

**Frontend**
- The browser `WebSocket` API — already abstracted in `useLiveStream.js`
  but read the
  [MDN WebSocket docs](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
  to understand `onopen`, `onmessage`, `onerror`, and `onclose` so you can
  debug connection issues.
- React `useReducer` — as the live feed gets more complex (filtering,
  pausing), `useReducer` is cleaner than multiple `useState` calls.
  Worth learning before you build the LiveFeed page.

---

## Phase 8 — Geo Map Page
**Goal:** The geo map page renders a D3 choropleth of source traffic by
country, with a hover tooltip and the country league table beneath it.

### Tasks
- [ ] Build the `GeoMap` page consuming `/analytics/geo`
- [ ] Render the world map using D3 + the `world-atlas` TopoJSON dataset
      (both already in `package.json`)
- [ ] Apply a colour scale (D3 `scaleSequential`) mapping packet count to
      fill colour
- [ ] Add hover tooltips showing country name and packet count
- [ ] Render the top countries bar chart and anomalous sources panel beneath
      the map

### Skills & libraries to learn

- [D3 — geographic projections](https://d3js.org/d3-geo/projection)
  Focus on `geoNaturalEarth1()`, `geoPath()`, and how to bind TopoJSON
  feature data to SVG `<path>` elements. The
  [Observable D3 map tutorial](https://observablehq.com/@d3/choropleth)
  is the best practical reference.
- [D3 — scales](https://d3js.org/d3-scale)
  Learn `scaleSequential` with `interpolateBlues` (or your colour of choice)
  to map a data domain to a colour range.
- [TopoJSON](https://github.com/topojson/topojson-client)
  One function: `topojson.feature(world, world.objects.countries)` converts
  the compact TopoJSON format into GeoJSON features D3 can render.
- D3 + React integration — D3 wants to own the DOM; React also wants to own
  the DOM. The cleanest pattern for a map is to use `useRef` on an `<svg>`
  element and let D3 render into it inside a `useEffect`. Read
  [this guide](https://2019.wattenberger.com/blog/react-and-d3) on the
  tradeoffs.

---

## Phase 9 — Polish, Testing & Hardening
**Goal:** The app is robust, handles errors gracefully, and is ready to be
demonstrated and written up.

### Tasks
- [ ] Add loading skeletons to every data-fetching component so there's no
      layout shift while queries resolve
- [ ] Add error boundaries — if one chart crashes it shouldn't take the whole
      dashboard with it
- [ ] Write FastAPI tests using `pytest` + `httpx.AsyncClient` for the auth,
      ingest, and analytics endpoints
- [ ] Add rate limiting to `/ingest` (e.g. 1000 requests/minute per API key)
      using `slowapi`
- [ ] Add request logging middleware to FastAPI using `starlette`'s
      `BaseHTTPMiddleware`
- [ ] Write a `README.md` documenting how to run the project, the API schema,
      and the ingest payload format — this doubles as dissertation appendix
      material
- [ ] (Optional) Dockerise the FastAPI app so the full stack runs with a
      single `docker compose up`

### Skills & libraries to learn

**Testing**
- [pytest](https://docs.pytest.org/en/stable/getting-started.html) —
  learn fixtures, `conftest.py`, and `pytest.mark.asyncio` for async tests.
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/) — required to
  `await` things in tests.
- [httpx `AsyncClient`](https://www.python-httpx.org/async/) — FastAPI's
  recommended test client for async apps. Use it with a test database
  (separate Postgres DB or SQLite in-memory).

**Reliability**
- [slowapi](https://github.com/laurents/slowapi) — a one-page integration
  with FastAPI that adds rate limiting via decorators. Good dissertation
  talking point around API abuse prevention.
- React `ErrorBoundary` — class components are still the only way to catch
  render errors. Learn the pattern once; it's always the same shape.

---

## Phase 10 — Dissertation Write-Up Angles
You don't need to build anything in this phase — it's a reference for what
to write about. Each architectural decision made during the build maps to
a section of the dissertation.

| Decision | What to write about |
|---|---|
| JWT + httpOnly refresh cookie | Stateless vs stateful auth, XSS/CSRF tradeoffs, token rotation strategy |
| API key hashing (SHA-256, prefix display) | Credential storage best practices, comparison with plaintext storage |
| In-memory access token (not localStorage) | XSS attack surface, browser storage security model |
| Anomaly scoring rules engine | Rules-based vs ML-based detection, precision/recall tradeoffs, threshold tuning |
| WebSocket broadcast architecture | Push vs pull, the `ConnectionManager` pattern, graceful degradation to polling |
| Postgres indexes on `(user_id, captured_at DESC)` | Query plan analysis, index design for time-series data |
| Bulk ingest vs per-entry insert | Throughput benchmarking — include actual numbers from your test script |
| `captured_at` vs `inserted_at` | Clock skew, out-of-order delivery, event time vs processing time |
| MaxMind GeoLite2 local DB | Privacy considerations of IP geolocation, accuracy limitations |
| TanStack Query stale time + refetch interval | Client-side caching strategy, balancing freshness vs server load |

---

## Dependency quick-reference

### Backend (`requirements.txt`)
```
fastapi
uvicorn[standard]
sqlalchemy[asyncio]
asyncpg
alembic
pydantic-settings
python-jose[cryptography]
passlib[bcrypt]
geoip2
slowapi
httpx
pytest
pytest-asyncio
```

### Frontend (`package.json` — already generated)
```
react + react-dom
react-router-dom
@tanstack/react-query
axios
recharts
d3
topojson-client
```

---

## Suggested weekly schedule (12 weeks)

| Week | Phase |
|---|---|
| 1 | Phase 1 — Environment & Foundations |
| 2 | Phase 2 — Authentication (backend) |
| 3 | Phase 2 — Authentication (frontend) |
| 4 | Phase 3 — API Key Management |
| 5 | Phase 4 — Log Ingestion |
| 6 | Phase 5 — Log History & Query API |
| 7 | Phase 6 — Analytics Endpoints |
| 8 | Phase 6 — Dashboard Charts (frontend) |
| 9 | Phase 7 — Real-Time WebSocket |
| 10 | Phase 8 — Geo Map Page |
| 11 | Phase 9 — Polish & Testing |
| 12 | Buffer / write-up / final demo prep |

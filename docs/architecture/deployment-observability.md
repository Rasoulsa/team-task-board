# Deployment, Nginx & Observability

This document describes the production-oriented container topology: multi-stage
image builds, the single-command Docker Compose stack, Nginx as the edge
serving the React SPA and proxying the API and WebSocket, and the optional
Prometheus + Grafana observability profile.

---

## Two compose files

The repository ships two Compose files with different purposes.

| File | Purpose | Frontend → Backend |
|---|---|---|
| `docker-compose.dev.yml` | Local development. Exposes host ports (Postgres `55432`, Redis `6380`, backend `8010`, frontend `5174`). Frontend talks directly to `http://localhost:8010`. | Direct, cross-origin (CORS) |
| `docker-compose.yml` | Production-like. Only Nginx (frontend) is published, on port `8080`. All other services are internal to the Compose network. Frontend talks to `/api` on the same origin. | Same-origin, proxied by Nginx |

Development:

```bash
docker compose -f docker-compose.dev.yml up --build
```

Production-like, one command:
```bash
docker compose up --build
```

### Image builds
#### Backend (`backend/Dockerfile`)

Multi-stage build:

1. **builder** — installs dependencies with `uv sync --frozen --no-dev` into a `.venv`, then installs the project.
2. **runtime** — copies the `.venv` and application code, installs only `curl` (for the healthcheck), and runs as a non-root `appuser`.

The runtime image contains no build tooling (`uv`, `pip`), reducing image size
and attack surface. A container-level `HEALTHCHECK` polls
`http://localhost:8000/health`.

The same image is reused for the `backend`, `celery-worker`, and `celery-beat`
services; only the `command` differs.

#### Frontend (`frontend/Dockerfile`)
Multi-stage build:

1. **build** — `node:20-alpine` runs `npm ci` and `npm run build`. Vite build arguments `VITE_API_URL` and `VITE_WS_URL` are set to relative paths (`/api/v1` and /`api/v1/ws`) so the browser always talks to the same origin it was served from.
2. **serve** — `nginx:1.27-alpine` serves the static `dist/` bundle on port `8080` and proxies API/WS traffic to the backend. `curl` is installed for the healthcheck.

---

## Why relative API/WS URLs

In development the frontend is built with absolute URLs
(`http://localhost:8010/api/v1`, `ws://localhost:8010/api/v1/ws`) because the
Vite dev server and backend run on different ports and origins.

In the production image the frontend is built with relative URLs. The
browser requests `/api/...` against the same origin (`http://localhost:8080`),
Nginx receives it, and proxies it to `backend:8000` inside the Compose network.
This removes CORS from the production path entirely and decouples the frontend
build from any specific backend host or port.

---

## Nginx routing

`frontend/nginx.conf` is mounted as an Nginx `conf.d` server block listening on
`8080`:

```text
| Location | Behavior |
|---|---|
| `/api/v1/ws/` | WebSocket proxy to `backend:8000` with `Upgrade`/`Connection` headers and long read/send timeouts (`3600s`) to keep sockets alive. |
| `/api/` | REST proxy to `backend:8000` with standard forwarded headers. |
| `/health` | Proxy to the backend liveness endpoint. |
| `/docs`, `/openapi.json` | Proxy to the backend's Swagger UI and OpenAPI schema (the backend mounts these at the root, not under `/api/v1`). |
| `/` | SPA fallback: `try_files $uri $uri/ /index.html` so client-side routes resolve to the React app. |
```

Nginx longest-prefix matching ensures `/api/v1/ws/` is matched before the
broader `/api/` block, so WebSocket upgrades are never handled by the plain
REST proxy.

> The backend serves Swagger UI at `/docs` and the schema at `/openapi.json`
> (app root), while all functional routes live under /api/v1. The explicit
> `/docs` and `/openapi.json` proxy blocks expose the interactive docs through
> the edge; remove them if you do not want docs publicly reachable in
> production.

---

## Service topology

```text
                      ┌─────────────────────────┐
  Browser  ─8080─▶    │  frontend (nginx)        │
                      │  serves SPA              │
                      │  proxies /api, /ws       │
                      └───────────┬─────────────┘
                                  │ (compose network)
                       ┌──────────▼──────────┐
                       │  backend (uvicorn)   │──▶ db (postgres)
                       │  /api/v1, /ws, /health│──▶ redis
                       │  /metrics             │
                       └──────────┬───────────┘
                                  │
              ┌───────────────────┼───────────────────┐
              ▼                   ▼                    ▼
      celery-worker         celery-beat            mailhog
      (redis broker)   (due-date sweep)        (SMTP capture)

  observability profile (optional):
      prometheus ──scrapes /metrics──▶ backend
      grafana    ──queries──▶ prometheus
```

Only the `frontend` service publishes a host port (`8080`). During development
`mailhog`’s UI (`8025`) and the observability ports (`9090`, `3000`) are also
published for inspection.

## Startup ordering and migrations

`db` and `redis` declare healthchecks; `backend`, `celery-worker`, and
`celery-beat` wait on `condition: service_healthy` before starting. This
prevents the connection-refused failures seen when workers start before Redis
is accepting connections.

The `backend` command runs migrations before serving:

```sh
sh -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"
```

A fresh `docker compose up` therefore self-migrates the database.

### Graceful shutdown

The FastAPI lifespan handler starts the Redis event bridge on startup and stops
it, then closes the Redis pool, on shutdown. Docker sends `SIGTERM` on
`docker compose down`; Uvicorn intercepts it and runs the lifespan shutdown,
allowing in-flight work and the Pub/Sub bridge to drain before the process
exits.

### Celery service healthchecks

The backend image defines an HTTP `HEALTHCHECK` against `/health`. Because the
`celery-worker` and `celery-beat` services reuse that image, they would inherit
an HTTP healthcheck that can never pass (Celery is not an HTTP server) and
report `unhealthy`. Both services therefore override it with:

```yaml
healthcheck:
  disable: true
```

A functional Celery liveness probe would be
`celery -A app.worker.celery_app.celery_app inspect ping`; disabling is chosen
for simplicity.

### Scaling workers

No service defines a fixed `container_name`, so Compose can run multiple
replicas of a service. To run three Celery workers:

```bash
docker compose up -d --scale celery-worker=3
docker compose ps | grep celery-worker   # three rows
```

Because the broker and result backend are Redis, workers coordinate through the
queue with no additional configuration.

### Observability profile

Prometheus and Grafana are gated behind the `observability` Compose profile so
the baseline stack stays lean:

```bash
# core stack only
docker compose up -d

# core stack + monitoring
docker compose --profile observability up -d
```

#### Metrics

The backend exposes Prometheus metrics at `/metrics` via
`prometheus-fastapi-instrumentator`, registered in the app factory and excluded
from the OpenAPI schema. Default metric families include:

- `http_requests_total` (by handler, method, status)
- `http_request_duration_seconds_bucket` (latency histogram)
- `http_requests_inprogress`

The `/metrics` and `/health` handlers are excluded from instrumentation to
avoid self-noise.

**Prometheus**

`docker/prometheus/prometheus.yml` scrapes `backend:8000/metrics` every 15s.
Targets are visible at `http://localhost:9090/targets`.

**Grafana**

Grafana is provisioned automatically from `docker/grafana/provisioning`:

- a Prometheus datasource pointing at `http://prometheus:9090`
- a “Backend Overview” dashboard (request rate, p95 latency, in-progress requests)

Reachable at `http://localhost:3000` (default `admin`/`admin`, overridable via
`GRAFANA_USER` / `GRAFANA_PASSWORD`). Generate traffic in the app first for the
panels to populate.

## Environment variables

Production-relevant variables (see `.env.example`):

```ini
POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB
SECRET_KEY, JWT_SECRET_KEY        # must be set; blank defaults are dev-only
CORS_ORIGINS=http://localhost:8080
GRAFANA_USER, GRAFANA_PASSWORD
```

Inside the production stack the backend connects to `db:5432` and `redis:6379`
over the Compose network; Celery uses Redis logical databases `/1` (broker) and
`/2` (result backend), matching the development configuration.


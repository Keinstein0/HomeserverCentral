# HomeserverCentral

A self-hosted homeserver stack built around a **Matrix homeserver (tuwunel)**, with
a **Matrix room-membership authentication gateway** protecting routes behind a
**Caddy** reverse proxy, a **SvelteKit static homepage**, and a **Go-based Status
API** for service health monitoring — all wired into an automated
**GitHub Actions CI/CD pipeline** with zero-downtime deploys.

```
                          ┌──────────────────────────────────────────┐
   Browser ──HTTPS──▶     │                Caddy (:443)              │
                          │  matrix.keinstein0.ch  → tuwunel:8008    │
                          │  status.keinstein0.ch  → status-api:5001 │
                          │  www.keinstein0.ch     → homepage:80     │
                          │        └── forward_auth ──▶              │
                          │        matrix-auth-gateway:5000 /verify  │
                          └──────────────────────────────────────────┘
```

## Architecture Overview

| Component | What it does | Location | Stack |
|---|---|---|---|
| **Matrix Auth Gateway** | Headless auth service. Validates user credentials against the Matrix homeserver, issues signed session cookies, and exposes `/verify` for Caddy's `forward_auth`. Access is granted based on **Matrix room membership** checked by a plain, unprivileged bot account. | `AuthService/` | Python 3.12 / Flask / gunicorn |
| **Status API** | Monitors the health of all services (Auth Gateway, tuwunel, Homepage, Caddy). Standard-library-only Go microservice with lazy TTL caching + singleflight stampede prevention. | `StatusAPI/` | Go 1.24 (stdlib only) |
| **Homepage** | SvelteKit static frontend. Also serves the shared auth pages (`login.html`, `403.html`, `404.html`) for all virtual hosts (micro-frontend pattern). | `Homepage/` | SvelteKit 2 / Vite 5 / Vitest |
| **Caddy** | Reverse proxy and TLS termination. Routes three virtual hosts, applies `forward_auth` Matrix gates to protected routes, serves Matrix well-known delegation, and proxies the deploy webhook. | `Caddy/Caddyfile` | Caddy 2.11 |
| **tuwunel** | The Matrix homeserver itself. Runs as a *separate* compose project and joins the `proxy-net` Docker network via `docker network connect` — not managed by this repo. | external | tuwunel (Synapse-compatible) |
| **tuwunel-mock** | Dependency-free Matrix homeserver mock (Python stdlib) used by the integration test suite. Only started under the `test` compose profile. | `tests/mock-tuwunel/` | Python (http.server) |

### How authentication works

1. A visitor hits a protected route (e.g. `status.keinstein0.ch`).
2. Caddy calls `GET /verify?room=status-viewers` on the Matrix Auth Gateway (`import matrix_gate "status-viewers"` in the Caddyfile).
3. **No session cookie** → `401` → Caddy redirects to `/login.html?redirect=…&room=…`.
   **Not a member of the required room** → `403` → Caddy serves the static `403.html`.
4. `/login.html` (served by the Homepage container) posts credentials to `POST /login` on the gateway, which validates them against the homeserver, stores a server-side session, and sets a signed cookie (`matrix_auth_session`).
5. On subsequent requests the gateway checks room membership via the bot account (cached for `MEMBERSHIP_CACHE_TTL` seconds) and returns `200` + `X-Auth-User` / `X-Auth-Power-Level` headers to Caddy.

The bot only ever sees membership of rooms it has been invited into and joined — no admin tokens, no OIDC.

## Repository Layout

```
HomeserverCentral/
├── AuthService/           # Matrix Auth Gateway (Flask) + unit tests (pytest)
├── StatusAPI/             # Status API (Go) + unit tests; designfile.md = architecture doc
├── Homepage/              # SvelteKit frontend + Vitest tests + static auth/error pages
├── Caddy/                 # Caddyfile with matrix_gate forward_auth snippets
├── tests/
│   ├── integration/       # End-to-end pytest suite (runs inside the compose network)
│   └── mock-tuwunel/      # Matrix homeserver mock (test profile only)
├── docker-compose.yml     # Dev/test stack (local builds, AUTO_HTTPS=off)
├── docker-compose.prod.yml# Production stack (GHCR images, external proxy-net)
├── .env.example           # Environment variable template
├── .env.test              # Deterministic dummy secrets for test runs
├── scripts/
│   ├── ci.sh              # Local CI runner — mirrors .github/workflows/ci.yml
│   └── deploy.sh          # Idempotent host-side deploy script (webhook target)
├── .github/workflows/
│   ├── ci.yml             # Lint → unit tests → integration tests
│   ├── build.yml          # Build & push images to GHCR (after CI passes on main)
│   └── deploy.yml         # Triggers the homeserver webhook after a successful build
├── TESTING.md             # Full testing specification & QA strategy
└── CONTINUOUS_DEPLOYMENT.md # CD architecture, security model & roadmap
```

## Virtual Hosts

| Host | Purpose | Auth |
|---|---|---|
| `matrix.keinstein0.ch` | Matrix client + federation traffic → `tuwunel:8008`; `.well-known/matrix/*` discovery | none (Matrix API) |
| `status.keinstein0.ch` | Status API UI/JSON → `status-api:5001` | gated: room `status-viewers` |
| `www.keinstein0.ch` | Public homepage → `homepage:80`; also hosts `POST /webhook/deploy` (deploy trigger, HMAC-signed) and `POST /login` / `GET /logout` auth endpoints | homepage public; `/api/status/*` gated |

## Development Setup

### Prerequisites

- Docker + Docker Compose
- Go 1.24, Python 3.12, Node.js 24 (for running unit tests locally — or just use `scripts/ci.sh`)

### 1. Environment

Copy `.env.example` to `.env` and fill in the required secrets:

```bash
cp .env.example .env
```

| Variable | Required | Description |
|---|---|---|
| `HOMESERVER_URL` | ✅ | Matrix homeserver URL, e.g. `http://tuwunel:8008` |
| `BOT_ACCESS_TOKEN` | ✅ | Access token for the plain bot account used for membership checks |
| `GATEWAY_SECRET_KEY` | ✅ | Random long string signing session cookies (e.g. `openssl rand -hex 32`) |
| `MATRIX_SERVER_NAME` | — | Server name used to expand bare usernames/aliases (default `keinstein0.ch`) |
| `COOKIE_DOMAIN` | — | Domain for the session cookie; leading dot covers subdomains (default `.keinstein0.ch`) |
| `SESSION_MAX_AGE` | — | Session duration in seconds (default 7 days) |
| `MEMBERSHIP_CACHE_TTL` | — | Membership-check cache TTL in seconds (default 60) |
| `CACHE_TTL_SECONDS` | — | Status API per-service result cache TTL (default 10) |
| `AUTO_HTTPS` | — | `off` for local dev/test → plain HTTP, no cert attempts |

### 2. Dev / Test stack (local builds)

```bash
docker compose --env-file .env up -d
```

- `matrix-auth-gateway` on `:5000`, `status-api` on `:5001`
- `homepage` serves the compiled SvelteKit bundle via nginx
- Caddy serves `http://localhost` (site labels are env-substituted, `AUTO_HTTPS=off`)

### 3. Production stack (GHCR images)

```bash
docker compose -f docker-compose.prod.yml --env-file .env up -d
```

Pulls pre-built images (`ghcr.io/keinstein0/{homepage,status-api,matrix-auth-gateway}:latest`) plus `caddy:2.11`, attaches to the external `proxy-net` network shared with the tuwunel homeserver container, and enables auto-HTTPS for the `*.keinstein0.ch` hosts.

### 4. Homepage live-reload (optional dev profile)

```bash
docker compose --profile dev up homepage-dev
```

Vite dev server on `:5173`, preview on `:4173`, source bind-mounted from `./Homepage`.

## Running the Services Locally (without Docker)

```bash
# Auth Service (Flask/gunicorn)
cd AuthService && pip install -r requirements.txt && python app.py   # :5000

# Status API (Go)
cd StatusAPI && go build ./cmd/statusapi && PORT=5001 ./statusapi    # :5001

# Homepage (SvelteKit dev server)
cd Homepage && npm install && npm run dev                            # :5173

# Caddy (dev config)
caddy run --config Caddy/Caddyfile
```

## Testing

Full details, test-scenario tables, and per-component instructions: see **[TESTING.md](./TESTING.md)**.

### One command for everything

```bash
bash scripts/ci.sh
```

Mirrors the GitHub Actions pipeline exactly: **lint → unit tests → integration tests** (spins up the containerized stack with the `tuwunel-mock`, runs the pytest suite *inside* the compose network against the production hostnames via Docker DNS aliases, then tears everything down).

### Unit tests per component

```bash
cd StatusAPI   && go test -v -race ./...                                              # Go unit tests
cd AuthService && pip install -r requirements.txt -r requirements-dev.txt && pytest -v # Flask tests
cd Homepage    && npm run check && npm run test                                        # svelte-check + Vitest
```

### Integration tests

```bash
docker compose --profile test --env-file .env.test up -d --build
docker compose --profile test --profile runner --env-file .env.test run --rm test-runner
```

Scenarios are grouped by ID (`INT-CAD-*` Caddy, `INT-AUT-*` auth gateway, `INT-STA-*` status API, `INT-HOM-*` homepage, `INT-CMP-*` compose config) — see `tests/integration/`.

## CI/CD

See **[CONTINUOUS_DEPLOYMENT.md](./CONTINUOUS_DEPLOYMENT.md)** for the full architecture and security model. In short — an asymmetric hybrid: heavy work (lint, tests, image builds) happens on GitHub Actions; the homeserver only pulls pre-built images.

```
git push main
  └─▶ CI (ci.yml): lint + unit + integration tests
        └─▶ Build (build.yml): build & push images to GHCR
              └─▶ Deploy (deploy.yml): HMAC-signed webhook POST to
                    https://www.keinstein0.ch/webhook/deploy
                          └─▶ host webhook runner executes scripts/deploy.sh:
                                git pull → docker compose pull → up -d → caddy reload (0 ms downtime)
```

- **Images published to GHCR:** `homepage`, `status-api`, `matrix-auth-gateway` (tagged `latest` + short SHA), with GHA layer caching.
- **Webhook security:** HMAC-SHA256 signature (`X-Hub-Signature-256`) verified by the receiver; GitHub-OIDC attestation is the planned upgrade.
- **Deploy script** (`scripts/deploy.sh`): idempotent, flock-guarded, only recreates changed containers and hot-reloads Caddy only if the Caddyfile changed.

## Documentation

| Document | Contents |
|---|---|
| [`TESTING.md`](./TESTING.md) | Testing strategy, unit-test scopes, and the full integration-scenario table |
| [`CONTINUOUS_DEPLOYMENT.md`](./CONTINUOUS_DEPLOYMENT.md) | CD architecture (micro-frontend hybrid), webhook security model, roadmap |
| [`StatusAPI/designfile.md`](./StatusAPI/designfile.md) | Status API architecture: checkers, caching, singleflight, registry |
| [`AuthService/whatisthis.md`](./AuthService/whatisthis.md) | Auth Gateway deep-dive: routes, flow, key design decisions |
| [`tests/mock-tuwunel/README.md`](./tests/mock-tuwunel/README.md) | Mock homeserver endpoints, test fixtures, and which scenarios it enables |
| [`DokumentationLB.md`](./DokumentationLB.md) | Project documentation (German) |

## Roadmap

Completed:
- ✅ Matrix Auth Gateway with room-membership-based forward auth
- ✅ Status API (Go) with health checkers, TTL cache, singleflight
- ✅ SvelteKit homepage serving shared auth/error pages (micro-frontend)
- ✅ Full CI pipeline (lint → unit → integration) locally and on GitHub Actions
- ✅ GHCR image publishing pipeline + production compose definition
- ✅ HMAC-signed deploy webhook route in Caddy + idempotent deploy script

Remaining (see `CONTINUOUS_DEPLOYMENT.md` §5 for details):
- [ ] Host webhook receiver daemon (e.g. `adnanh/webhook`) — deploy.sh and the Caddy route already exist
- [ ] GitHub OIDC attestation as an alternative/fallback to HMAC signatures
- [ ] Caddy-side GitHub runner IP range filtering & rate-limiting for the webhook route
- [ ] End-to-end dry run of the automated deploy on `main` with zero Matrix disruption


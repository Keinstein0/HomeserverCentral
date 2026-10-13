# Testing Specification & QA Strategy

This document outlines the testing strategy for HomeserverCentral, detailing the pre-testing project adjustments, unit testing instructions per component, and integration test scenarios across the full container stack.

---

## 1. Pre-Testing Preparations & Project Adjustments

Before running automated unit and integration test suites, the following configuration and environment adjustments are required.

### 1.1 Caddyfile Adjustments
1. **Protect Status API Endpoint via Forward Auth**:
   Wrap the Status API route with `import matrix_gate "status-viewers"` so that unauthorized visitors cannot inspect infrastructure status.
2. **Local HTTP-friendly Redirects**:
   In the `(matrix_gate)` snippet, change the hardcoded `https://{host}/login.html...` redirect to a scheme-aware or relative redirect (`/login.html?redirect={http.request.orig_uri}&room={args[0]}`). This prevents connection timeouts when running automated tests locally over plain HTTP (`http://localhost` with `AUTO_HTTPS=off`).
3. **Local Route for Status Testing**:
   Ensure a local path (such as `handle /api/status/*` or `status.localhost`) is mapped to `status-api:5001` so test runners can execute integration requests against `localhost` without requiring custom DNS overrides.
4. **Static Auth & Error Pages**:
   Ensure `login.html`, `403.html`, and `404.html` exist in `Homepage/static` so forward_auth error and redirect handlers resolve valid HTML pages.

### 1.2 Docker Compose Configuration
1. **Tuwunel Mock Service with Profile**:
   Add a lightweight Matrix homeserver mock container to `docker-compose.yml` configured under the `test` (and/or `dev`) profile:
   ```yaml
   tuwunel-mock:
     build:
       context: ./tests/mock-tuwunel
     container_name: tuwunel-mock
     networks:
       homeserver_internal:
         aliases:
           - tuwunel
     profiles:
       - test
   ```
   *Behavior*:
   - In **Production** (`docker compose up -d`): The mock container is ignored; services connect to the real Matrix homeserver.
   - In **Test / Dev** (`docker compose --profile test up -d`): The mock starts and resolves as `tuwunel:8008` over the internal network.

2. **Test Environment File (`.env.test`)**:
   Provide deterministic dummy secrets for CI and local test runs:
   ```env
   GATEWAY_SECRET_KEY=test_secret_key_12345
   BOT_ACCESS_TOKEN=test_bot_token_abcde
   HOMESERVER_URL=http://tuwunel:8008
   AUTO_HTTPS=off
   ```

---

## 2. Unit Testing Instructions (Phase 1)

Unit tests run isolated from the network, with zero external dependencies, executing in seconds.

### 2.1 Status API (Go)
- **Scope**:
  - `internal/checker`: Unit tests using `httptest.Server` verifying `UP`, `DOWN`, and timeout parsing.
  - `internal/cache`: Stampede prevention and TTL expiry tests using `singleflight`.
  - `internal/registry`: Registration, lookup, and duplicate ID handling.
  - `internal/server`: HTTP status handlers for `/healthz`, `/services`, and `/services/{id}`.
- **Execution Command**:
  ```bash
  cd StatusAPI
  go test -v -race ./...
  ```
  *(Or inside Docker if Go is not installed on the host runner):*
  ```bash
  docker run --rm -v "$PWD/StatusAPI:/app" -w /app golang:1.24-alpine go test -v -race ./...
  ```

### 2.2 Auth Service (Python / Flask)
- **Scope**:
  - Session cookie generation, cryptographic signing, and expiration verification.
  - Route authorization logic (`/verify`) using mocked HTTP responses (via `unittest.mock` or `responses`).
  - Room membership caching and cache eviction behavior.
  - Negative tests: invalid signatures, expired sessions, malformed room IDs.
- **Execution Command**:
  ```bash
  cd AuthService
  pytest -v tests/
  ```

### 2.3 Homepage (SvelteKit / Vite)
- **Scope**:
  - Svelte component rendering and reactive state updates.
  - Store and helper utility unit tests via Vitest.
  - Static build validation (`npm run check` and `npm run build`).
- **Execution Command**:
  ```bash
  cd Homepage
  npm run check
  npm run test # (Vitest suite)
  ```

---

## 3. Integration Testing Scenarios (Phase 2)

Integration tests spin up the containerized stack using `docker compose --profile test up -d` and execute end-to-end HTTP scenarios through Caddy and internal networks.

### Integration Test Scenarios Table

| Scenario ID | Component / Area | Test Scenario | Description / Verification | Expected Result |
|---|---|---|---|---|
| **INT-CAD-01** | Caddy | Ingress & Startup Health | Verify Caddy parses Caddyfile and starts without syntax errors. Probe `GET /_matrix/client/.well-known/matrix/client`. | HTTP 200 OK with valid Matrix discovery JSON payload. |
| **INT-CAD-02** | Caddy | Public Static Assets | Request public files (`/login.html`, `/assets/*`). | HTTP 200 OK; no forward_auth redirection triggered. |
| **INT-CAD-03** | Caddy | Forward Auth Redirection | Request a protected route without session cookies (e.g. `/` or protected `/status`). | HTTP 302 Redirect to `/login.html?redirect=...`. |
| **INT-CAD-04** | Caddy | Header Security | Inspect response headers from Caddy on `localhost`. | `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Server` header stripped. |
| **INT-AUT-01** | Auth Gateway | Gateway Self-Health | Probe `GET http://matrix-auth-gateway:5000/healthz` (or via Caddy `/healthz` if mapped). | HTTP 200 OK; response status `"ok"`. |
| **INT-AUT-02** | Auth Gateway | Valid Login Flow | `POST /login` with valid credentials of a user belonging to the required room (against `tuwunel-mock`). | HTTP 302 redirect with valid signed session cookie in `Set-Cookie`. |
| **INT-AUT-03** | Auth Gateway | Invalid Credentials | `POST /login` with incorrect password or invalid username. | HTTP 302 redirect to `/login.html?error=1` (or 401/403); no session cookie issued. |
| **INT-AUT-04** | Auth Gateway | Unauthorized Member (403) | Attempt access to protected route with session of a user NOT in the required room. | Forward auth returns HTTP 403 Forbidden; Caddy displays `403.html`. |
| **INT-AUT-05** | Auth Gateway | Logout Flow | `GET /logout` with an active session cookie. | Session invalidated in gateway; `Set-Cookie` expired; subsequent protected requests redirect to `/login.html`. |
| **INT-STA-01** | Status API | Service Self-Health | Probe `GET http://localhost:5001/healthz`. | HTTP 200 OK; status indicates Status API is running. |
| **INT-STA-02** | Status API | Service Discovery | Probe `GET /services` on Status API. | HTTP 200 OK; returns array of registered service IDs (`auth-gateway`, `tuwunel`, `homepage`, `caddy`). |
| **INT-STA-03** | Status API | Live Status Probe (Healthy) | Probe `GET /services/auth-gateway` and `GET /services/tuwunel` with mock running. | HTTP 200 OK; `"status": "UP"` with recorded response time. |
| **INT-STA-04** | Status API | Live Status Probe (Degraded/Down) | Temporarily simulate downstream failure on mock homeserver and query `GET /services/tuwunel`. | HTTP 200 OK; `"status": "DOWN"` or `"DEGRADED"`. |
| **INT-STA-05** | Status API | Cache Buffer & Burst Protection | Send 10 concurrent requests to `/services/auth-gateway` within TTL buffer window ($N$ seconds). | All requests return identical cached `last_checked` timestamp; downstream service pinged only once. |
| **INT-STA-06** | Status API | Protected Status Access | Attempt to access Status API through Caddy protected route without login cookie. | HTTP 302 Redirect to `/login.html`. Access granted with valid session cookie. |
| **INT-HOM-01** | Homepage | Static Build Delivery | Caddy serves static production build of Homepage from `/apps/homepage`. | HTTP 200 OK for `index.html`; static assets load with correct MIME types (`text/html`, `application/javascript`). |
| **INT-CMP-01** | Docker Compose | Compose Config Validation | Run `docker compose config` and `docker compose --profile test config`. | Configuration validates with exit code 0; volume/network references resolve cleanly. |
| **INT-CMP-02** | Docker Compose | Healthcheck Cascading | Verify startup order: `caddy` and `status-api` wait until `matrix-auth-gateway` reports `healthy`. | Services transition to `healthy` state without restarting or crashing. |

---

## 4. Execution Workflow

### Automated CI Pipeline Sequence
1. **Lint & Static Analysis**:
   - `golangci-lint` (Status API)
   - `flake8` / `black` (Auth Service)
   - `svelte-check` / `eslint` (Homepage)
2. **Run Unit Tests**:
   - Go unit tests (`go test -v -race ./...`)
   - Python unit tests (`pytest`)
   - SvelteKit tests (`vitest run`)
3. **Build & Spin Up Test Containers**:
   ```bash
   docker compose --profile test up -d --build
   ```
4. **Wait for Healthchecks**:
   Poll container health until `matrix-auth-gateway`, `status-api`, and `caddy` are all healthy.
5. **Run Integration Suite**:
   Execute integration test script (using `pytest` or Go test runner) asserting scenarios `INT-CAD-01` through `INT-CMP-02`.
6. **Teardown**:
   ```bash
   docker compose --profile test down -v
   ```

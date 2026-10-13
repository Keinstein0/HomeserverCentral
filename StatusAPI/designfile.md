# Status API - Architecture & Design Document

## 1. Overview
The **Status API** is a lightweight, standalone microservice written in **Go**. Its role is to monitor and report the health and operational status of all services running inside the HomeserverCentral ecosystem (e.g., Matrix Auth Gateway, Matrix Homeserver / Tuwunel, Homepage, Caddy).

The key principles are:
- **Simplicity**: Minimal overhead, fast execution, small Docker container footprint.
- **Modularity (Polymorphism via Interfaces)**: Each target service is modeled independently to encapsulate its custom check logic.
- **Lazy On-Demand Caching**: No persistent background polling when idle; requests serve cached results within an $N$-second TTL buffer to prevent downstream request spamming and thundering herds.

---

## 2. Core Abstractions & Interfaces

In Go, polymorphism is implemented using interfaces. Each monitored service implements the `ServiceChecker` interface.

### Status Enum & Result Model
```go
type Status string

const (
    StatusOK       Status = "UP"
    StatusDegraded Status = "DEGRADED"
    StatusDown     Status = "DOWN"
)

type CheckResult struct {
    ID             string                 `json:"id"`
    Name           string                 `json:"name"`
    Status         Status                 `json:"status"`
    ResponseTimeMs int64                  `json:"response_time_ms"`
    Message        string                 `json:"message,omitempty"`
    Details        map[string]interface{} `json:"details,omitempty"`
    LastChecked    time.Time              `json:"last_checked"`
}
```

### The `ServiceChecker` Interface
```go
type ServiceChecker interface {
    ID() string
    Name() string
    Check(ctx context.Context) CheckResult
}
```

---

## 3. Concrete Checker Implementations

Each component in the infrastructure has a dedicated checker struct:

1. **`AuthServiceChecker`**
   - Probes `http://matrix-auth-gateway:5000/healthz`.
   - Validates response code, JSON payload, and upstream Matrix connectivity indicators.
2. **`MatrixHomeserverChecker` (Tuwunel)**
   - Queries `http://tuwunel:8008/_matrix/client/versions`.
   - Verifies homeserver core responsiveness.
3. **`HomepageChecker` / `CaddyChecker`**
   - Validates ingress routing and frontend reachability.
4. **`HTTPHealthChecker` (Generic Base)**
   - Reusable checker parameterized by target URL, HTTP method, timeout, and expected status code, which custom checkers can embed or reuse.

---

## 4. Caching & Stampede Prevention (Lazy TTL Buffer)

Instead of continuous background polling loops, the service uses an **on-demand cached decorator** pattern:

```
Incoming Request (GET /services/:id)
               │
               ▼
      [CachedChecker Wrapper]
               │
      Is cache younger than TTL (e.g., 10s)?
      ├── YES ──► Return cached CheckResult immediately
      └── NO  ──► Acquire singleflight lock
                    │
                    ├── Probe downstream service Check(ctx)
                    ├── Update in-memory cache & timestamp
                    └── Return fresh CheckResult
```

### Concurrency & Stampede Handling:
- **`singleflight.Group`**: When multiple requests hit an expired cache concurrently, only one downstream health probe is executed; other concurrent requests wait and share the result.
- **Lazy Evaluation**: If no traffic comes in, zero CPU cycles or network calls are wasted on health probing.
- **Configurable TTL**: Global default via environment variable (`CACHE_TTL_SECONDS`), with optional per-service overrides.

---

## 5. Registry & Routing

A thread-safe `Registry` holds all registered `ServiceChecker` instances.

```go
type Registry struct {
    checkers map[string]ServiceChecker
}
```

### Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/services` | Returns list of all registered service IDs and metadata. |
| `GET` | `/services/{id}` | Returns health status for the specified service (cached or live). |
| `GET` | `/healthz` | Self-health check for the Status API container itself. |
| `GET` | `/status` *(optional)* | Aggregated status of all services executed concurrently. |

#### Sample Responses

**`GET /services`**
```json
[
  { "id": "auth-gateway", "name": "Matrix Auth Gateway" },
  { "id": "tuwunel", "name": "Matrix Homeserver" },
  { "id": "homepage", "name": "Svelte Frontend" }
]
```

**`GET /services/auth-gateway`**
```json
{
  "id": "auth-gateway",
  "name": "Matrix Auth Gateway",
  "status": "UP",
  "response_time_ms": 14,
  "last_checked": "2026-10-13T08:30:00Z"
}
```

---

## 6. Docker & Environment Configuration

### Dockerfile
- Multi-stage build:
  - **Builder stage**: `golang:1.24-alpine` (compiles a statically linked CGO-disabled binary).
  - **Runtime stage**: `scratch` or `alpine` for minimal image size (~10–15 MB).

### Compose Integration (`docker-compose.yml`)
- Service name: `status-api`
- Port: `5001:5001`
- Environment variables:
  - `PORT=5001`
  - `CACHE_TTL_SECONDS=10`
  - `AUTH_SERVICE_URL=http://matrix-auth-gateway:5000`
  - `HOMESERVER_URL=http://tuwunel:8008`

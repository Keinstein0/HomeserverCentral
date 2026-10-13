# Status API

A lightweight, standalone Go microservice that monitors and reports the health
of all services in the HomeserverCentral ecosystem (Matrix Auth Gateway, Matrix
Homeserver / Tuwunel, Homepage, Caddy).

See [`designfile.md`](./designfile.md) for the full architecture document.

## Principles

- **Simplicity** — standard library only, no external dependencies, tiny image.
- **Modularity** — each target service implements the `ServiceChecker` interface.
- **Lazy on-demand caching** — no background polling; results are cached within
  an N-second TTL and concurrent cache misses collapse to a single downstream
  probe (singleflight).

## Endpoints

| Method | Endpoint          | Description                                            |
|--------|-------------------|-------------------------------------------------------|
| `GET`  | `/healthz`        | Self-health of the Status API container.             |
| `GET`  | `/services`       | List of all registered service IDs and names.         |
| `GET`  | `/services/{id}` | Health status for one service (cached or live).       |
| `GET`  | `/status`         | Aggregated status of all services (run concurrently). |

## Environment variables

| Variable             | Default                              | Description                          |
|----------------------|--------------------------------------|--------------------------------------|
| `PORT`               | `5001`                               | Listen port.                         |
| `CACHE_TTL_SECONDS`  | `10`                                 | Per-service result cache TTL.        |
| `AUTH_SERVICE_URL`    | `http://matrix-auth-gateway:5000`    | Matrix Auth Gateway base URL.        |
| `HOMESERVER_URL`     | `http://tuwunel:8008`                | Matrix homeserver base URL.          |
| `HOMEPAGE_URL`       | `http://homepage:5173`               | Homepage (Svelte frontend) URL.      |
| `CADDY_URL`          | `http://caddy`                       | Caddy reverse proxy URL.             |

## Project layout

```
StatusAPI/
  cmd/statusapi/main.go            # entrypoint: env wiring, registry, server
  internal/
    checker/                       # Status, CheckResult, ServiceChecker, checkers
    cache/                         # lazy TTL cache + singleflight decorator
    registry/                      # thread-safe checker registry
    server/                        # HTTP handlers and graceful shutdown
  Dockerfile                       # multi-stage build (golang:1.24-alpine -> alpine)
  designfile.md                    # architecture & design document
```

## Build & run locally

```bash
cd StatusAPI
go build ./cmd/statusapi
PORT=5001 CACHE_TTL_SECONDS=10 ./statusapi
```

## Test

```bash
cd StatusAPI
go test -race ./...
```

## Adding a new checker

1. Implement the `checker.ServiceChecker` interface
   (`ID()`, `Name()`, `Check(ctx)`). For HTTP targets, reuse
   `checker.NewHTTPHealthChecker(...)` with a `WithBodyValidator(...)` option.
2. In `cmd/statusapi/main.go`, register a cached wrapper:
   `register(checker.NewMyChecker(url))`.
3. (Optional) Add a `MY_SERVICE_URL` env var with a sensible default.

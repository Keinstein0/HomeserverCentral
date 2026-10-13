# mock-tuwunel

A tiny, dependency-free mock of a Matrix (Synapse-compatible) homeserver,
activated only under the `test` compose profile. It lets unit and
integration tests run without the production tuwunel instance or custom
DNS overrides.

## Why it exists

The real services in HomeserverCentral talk to a Matrix homeserver at
`HOMESERVER_URL` (default `http://tuwunel:8008`). Under the `test` profile
the `tuwunel-mock` container registers the network alias `tuwunel`, so
that same URL resolves to the mock. No service configuration changes are
required.

## What it implements

Built with the Python standard library only (`http.server`) — no Flask,
no external packages — so the image is small and deterministic.

| Endpoint | Method | Behaviour |
|---|---|---|
| `/_matrix/client/versions` | GET | `200 {"versions":["v1.0","v1.1"]}` (drives StatusAPI `MatrixHomeserverChecker`). |
| `/_matrix/client/v3/login` | POST | `200` with `access_token` + `user_id` for known users; `403 M_FORBIDDEN` otherwise (drives AuthService login). |
| `/_matrix/client/v3/directory/room/<alias>` | GET | `200 {"room_id":...}` for known aliases; `404` otherwise (AuthService `resolve_room_id`). |
| `/_matrix/client/v3/rooms/<room_id>/joined_members` | GET | `200 {"joined":{...}}` for known rooms (AuthService membership check). |
| `/_matrix/client/v3/rooms/<room_id>/state/m.room.power_levels` | GET | `200` power-level event for known rooms (AuthService power-level lookup). |
| `/` , `/healthz` | GET | `200` self-reachability probe. |
| anything else | * | `404 M_UNRECOGNIZED`. |

## Test fixtures (hard-coded)

**Users** (`username`/`password` → canonical `user_id`):

| username | password | user_id | member of `status-viewers`? |
|---|---|---|---|
| `alice` | `password` | `@alice:keinstein0.ch` | ✅ yes (power 50) |
| `bob`   | `password` | `@bob:keinstein0.ch`   | ❌ no |

**Rooms**:

| alias | room_id | joined members |
|---|---|---|
| `#status-viewers:keinstein0.ch` | `!statusroom:keinstein0.ch` | `@alice:keinstein0.ch` (power 50), `@admin:keinstein0.ch` (power 100) |

## Scenarios this enables

- **INT-AUT-02** — valid login flow: `alice` logs in → signed cookie → access to protected `status-viewers` route granted.
- **INT-AUT-03** — invalid credentials: wrong user/password → `403 M_FORBIDDEN` → AuthService redirects to `/login.html?error=invalid_credentials`.
- **INT-AUT-04** — unauthorized member: `bob` logs in OK but is not in `status-viewers` → forward_auth returns `403` → Caddy serves `403.html`.
- **INT-STA-03** — live status probe (healthy): StatusAPI `MatrixHomeserverChecker` hits `/_matrix/client/versions` → `UP`.

## Running

The mock is started automatically by compose under the test profile:

```bash
docker compose --profile test --env-file .env.test up -d --build
```

It can also be run directly for local debugging:

```bash
cd tests/mock-tuwunel
python3 mock.py          # listens on 0.0.0.0:8008
```

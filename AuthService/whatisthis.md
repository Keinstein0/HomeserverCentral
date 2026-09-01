# AuthService — Matrix Auth Gateway

## What it is
A minimal Flask-based authentication gateway that replaces `oauth2-proxy` for a homeserver deployed via Caddy. It authenticates users directly against a Matrix/Synapse homeserver and enforces room-based access control using a plain, unprivileged bot account. It exposes a `/verify` endpoint that Caddy's `forward_auth` directive calls on every protected request.

**No admin tokens, no OIDC, no matrix-user-verification-service.** The bot only ever sees membership of rooms it has been invited into and joined — it cannot read or affect anything else on the server.

## What it does

### Core routes
| Endpoint | Method | Purpose |
|---|---|---|
| `/login` | POST | Validates credentials against the Matrix homeserver, creates a server-side session keyed by a random ID, sets a signed cookie (`matrix_auth_session`), then 302-redirects back to `redirect`. The login form itself is served by Caddy as a static page — this endpoint is a headless API/redirect target only. |
| `/verify?room=X` | GET | Called by Caddy on every request to a protected path. Validates the session cookie, then (with short-lived caching) asks the bot account to list room X's joined members and checks whether the session's user is in it. Returns `200` + `X-Auth-User` / `X-Auth-Power-Level` headers if authorized, or `401`/`403` otherwise. If called without a `room` arg, being logged in at all is sufficient. |
| `/logout` | GET | Clears the session and redirects to `/login.html`. |
| `/healthz` | GET | Simple health-check endpoint. |

### How it works
1. **Login:** User submits credentials via Caddy's static `/login.html` → `POST /login` → `matrix_login()` hits the homeserver's `_matrix/client/login` → session stored in-memory → signed cookie set.
2. **Verify:** Caddy calls `GET /verify?room=!xyz:domain` → cookie validated via `itsdangerous` → membership cached for `MEMBERSHIP_CACHE_TTL` seconds (default 60) → bot checks room members via `/rooms/{room_id}/state/m.join` or `/joined_members` → returns access decision.
3. **Logout:** Cookie validated and session removed from the in-memory store.

### Key details
- **In-memory session store + membership cache** (fine for a single-instance homelab; lost on restart — users just log in again). Swap to Redis for multi-replica deployments.
- **Alias cache** resolves room aliases (`#room:domain` → `!roomid:domain`) indefinitely since aliases essentially never change.
- **Dependencies:** Flask 3.0.3, requests 2.32.3, itsdangerous 2.2.0, gunicorn 22.0.0.
- **Docker:** Python 3.12-slim, gunicorn on port 5000 (`-w 1 --threads 4`).
- **Required env vars:** `HOMESERVER_URL`, `BOT_ACCESS_TOKEN`, `GATEWAY_SECRET_KEY`.
- **Optional env vars:** `MATRIX_SERVER_NAME`, `SESSION_MAX_AGE` (default 7 days), `MEMBERSHIP_CACHE_TTL` (default 60s).

## Why it exists
To gate Matrix-hosted web content behind room-membership checks without running a full OAuth2 proxy, avoiding the complexity of OIDC client registration and admin-token delegation.

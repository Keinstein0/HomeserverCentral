#!/usr/bin/env python3
"""
mock-tuwunel
------------
A tiny, deterministic, in-memory mock of a Matrix (Synapse-compatible)
homeserver, used by the HomeserverCentral test/dev profile so that unit
and integration tests never need the production tuwunel instance or
custom DNS.

It speaks just enough of the Matrix Client-Server API to satisfy the two
real callers in this project:

  - AuthService/app.py
        POST /_matrix/client/v3/login
        GET  /_matrix/client/v3/directory/room/<alias>
        GET  /_matrix/client/v3/rooms/<room_id>/joined_members
        GET  /_matrix/client/v3/rooms/<room_id>/state/m.room.power_levels

  - StatusAPI/internal/checker/checkers.go
        GET  /_matrix/client/versions

No state is persisted; everything is hard-coded so test runs are fully
reproducible. Listens on 0.0.0.0:8008 (the same port the real tuwunel
uses, so HOMESERVER_URL=http://tuwunel:8008 is honoured unchanged).

Test fixtures
-------------
Users (username/password -> canonical user_id):
    alice / password -> @alice:keinstein0.ch   (MEMBER of status-viewers)
    bob   / password -> @bob:keinstein0.ch     (NOT a member)

Rooms:
    #status-viewers:keinstein0.ch  ->  !statusroom:keinstein0.ch
    joined members:  @alice:keinstein0.ch (power 50),
                     @admin:keinstein0.ch  (power 100)

Scenarios enabled:
    - INT-AUT-02: valid login (alice) -> 302 + signed cookie.
    - INT-AUT-03: invalid credentials -> 403 M_FORBIDDEN -> login error.
    - INT-AUT-04: bob logs in but is NOT in status-viewers -> 403.
    - INT-STA-03: GET /_matrix/client/versions -> 200 {"versions":[...]}.
"""

import json
import logging
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, unquote

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("mock-tuwunel")

PORT = int(os.environ.get("PORT", "8008"))
SERVER_NAME = "keinstein0.ch"

# --------------------------------------------------------------------------
# Deterministic test fixtures
# --------------------------------------------------------------------------

# username -> (password, canonical user_id). Both users authenticate
# successfully; only alice is a member of the gated status-viewers room.
USERS = {
    "alice": ("password", "@alice:keinstein0.ch"),
    "bob":   ("password", "@bob:keinstein0.ch"),
}

# room alias -> room_id
ROOM_ALIASES = {
    "#status-viewers:keinstein0.ch": "!statusroom:keinstein0.ch",
}

# room_id -> { joined, power_levels }
ROOMS = {
    "!statusroom:keinstein0.ch": {
        "joined": {
            "@alice:keinstein0.ch": {"display_name": "alice"},
            "@admin:keinstein0.ch": {"display_name": "admin"},
        },
        "power_levels": {
            "users_default": 0,
            "users": {
                "@alice:keinstein0.ch": 50,
                "@admin:keinstein0.ch": 100,
            },
        },
    },
}

# --------------------------------------------------------------------------
# Test-only admin controls (not part of the Matrix API)
# --------------------------------------------------------------------------
# These let integration tests simulate downstream failure (INT-STA-04) and
# verify cache burst protection / request counting (INT-STA-05). They are
# reached via /__admin/* on the mock's published port (8008).

import threading

# When True, /_matrix/client/versions returns 500 (simulates a down
# homeserver) for INT-STA-04.
FAILURE_MODE = False
# Counts how many times each endpoint family was hit, for INT-STA-05.
REQUEST_COUNTS = {
    "versions": 0,
    "login": 0,
    "directory": 0,
    "joined_members": 0,
    "power_levels": 0,
}
_state_lock = threading.Lock()

# --------------------------------------------------------------------------
# Response helpers
# --------------------------------------------------------------------------

def send_json(handler, status, payload):
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.end_headers()
    handler.wfile.write(body)


def send_error_json(handler, status, errcode, error):
    send_json(handler, status, {"errcode": errcode, "error": error})


# --------------------------------------------------------------------------
# Request handler
# --------------------------------------------------------------------------

class MockHandler(BaseHTTPRequestHandler):
    server_version = "mock-tuwunel/1.0"

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0) or 0)
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        path = unquote(urlparse(self.path).path)
        log.info("GET %s", path)

        # --- Admin: stats / reset_stats (GET) ---------------------------
        if path == "/__admin/stats":
            with _state_lock:
                send_json(self, 200, dict(REQUEST_COUNTS))
            return
        if path == "/__admin/fail_mode":
            with _state_lock:
                send_json(self, 200, {"failure_mode": FAILURE_MODE})
            return

        # --- Status API: MatrixHomeserverChecker -----------------------
        if path == "/_matrix/client/versions":
            with _state_lock:
                REQUEST_COUNTS["versions"] += 1
                fail = FAILURE_MODE
            if fail:
                send_error_json(self, 500, "M_UNKNOWN", "Simulated downstream failure")
                return
            send_json(self, 200, {"versions": ["v1.0", "v1.1"]})
            return

        # --- Self reachability probe -----------------------------------
        if path == "/" or path == "/healthz":
            send_json(self, 200, {"server": "mock-tuwunel", "status": "ok"})
            return

        # --- Room alias resolution (AuthService.resolve_room_id) -------
        prefix = "/_matrix/client/v3/directory/room/"
        if path.startswith(prefix):
            with _state_lock:
                REQUEST_COUNTS["directory"] += 1
            alias = path[len(prefix):]
            room_id = ROOM_ALIASES.get(alias)
            if room_id:
                send_json(self, 200, {"room_id": room_id})
            else:
                send_error_json(self, 404, "M_NOT_FOUND", f"Unknown room alias: {alias}")
            return

        # --- Room endpoints (joined_members, power_levels) --------------
        prefix = "/_matrix/client/v3/rooms/"
        if path.startswith(prefix):
            rest = path[len(prefix):]
            if rest.endswith("/joined_members"):
                with _state_lock:
                    REQUEST_COUNTS["joined_members"] += 1
                room_id = rest[: -len("/joined_members")]
                room = ROOMS.get(room_id)
                if room is not None:
                    send_json(self, 200, {"joined": room["joined"]})
                else:
                    send_error_json(self, 404, "M_NOT_FOUND", "Unknown room")
                return
            if rest.endswith("/state/m.room.power_levels"):
                with _state_lock:
                    REQUEST_COUNTS["power_levels"] += 1
                room_id = rest[: -len("/state/m.room.power_levels")]
                room = ROOMS.get(room_id)
                if room is not None:
                    send_json(self, 200, room["power_levels"])
                else:
                    send_error_json(self, 404, "M_NOT_FOUND", "Unknown room")
                return
            send_error_json(self, 404, "M_UNRECOGNIZED", f"Unknown room endpoint: {path}")
            return

        send_error_json(self, 404, "M_UNRECOGNIZED", f"Unknown endpoint: {path}")

    def do_POST(self):
        path = unquote(urlparse(self.path).path)
        log.info("POST %s", path)

        global FAILURE_MODE

        # --- Admin: fail / recover / reset_stats (POST) -----------------
        if path == "/__admin/fail":
            with _state_lock:
                FAILURE_MODE = True
            send_json(self, 200, {"failure_mode": True})
            return
        if path == "/__admin/recover":
            with _state_lock:
                FAILURE_MODE = False
            send_json(self, 200, {"failure_mode": False})
            return
        if path == "/__admin/reset_stats":
            with _state_lock:
                for k in REQUEST_COUNTS:
                    REQUEST_COUNTS[k] = 0
            send_json(self, 200, {"reset": True})
            return

        # --- Login (AuthService.matrix_login) --------------------------
        if path == "/_matrix/client/v3/login":
            with _state_lock:
                REQUEST_COUNTS["login"] += 1
            body = self._read_body()
            identifier = body.get("identifier", {}) or {}
            user = identifier.get("user", "")
            password = body.get("password", "")

            # Accept both bare "alice" and full "@alice:keinstein0.ch".
            local = user[1:].split(":", 1)[0] if user.startswith("@") else user

            entry = USERS.get(local)
            if entry is not None and entry[0] == password:
                user_id = entry[1]
                send_json(self, 200, {
                    "user_id": user_id,
                    "access_token": f"mock_token_{local}",
                    "home_server": SERVER_NAME,
                    "device_id": f"DEV{local.upper()}",
                })
            else:
                # Mirrors Synapse: 403 M_FORBIDDEN on bad credentials.
                send_error_json(self, 403, "M_FORBIDDEN", "Invalid username or password")
            return

        send_error_json(self, 404, "M_UNRECOGNIZED", f"Unknown endpoint: {path}")

    # Route the default stderr logging through our logger for clarity.
    def log_message(self, fmt, *args):
        log.info("%s - %s", self.address_string(), fmt % args)


def main():
    server = ThreadingHTTPServer(("0.0.0.0", PORT), MockHandler)
    log.info("mock-tuwunel listening on 0.0.0.0:%d", PORT)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("shutting down")
        server.shutdown()


if __name__ == "__main__":
    main()

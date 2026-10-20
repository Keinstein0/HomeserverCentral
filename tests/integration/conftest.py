"""
Integration test suite for HomeserverCentral (Phase 2 / TESTING.md §3).

pytest runs INSIDE the compose network (docker compose --profile test run
--rm test-runner, orchestrated by scripts/ci.sh or the CI workflow). This
is what lets the suite use the real production hostnames: matrix, status
and www .keinstein0.ch are Docker DNS aliases of the local Caddy container
(see docker-compose.yml), so requests exercise the exact production
virtual hosts — no host-level DNS overrides, no test-only Caddyfile
routes, no redundant well-known mirrors.

The compose lifecycle (up -> run -> down) is owned by the caller; this
module only waits for readiness before yielding to the tests.

Run the full suite via:  bash scripts/ci.sh
"""

import os
import time

import pytest
import requests


# ---------------------------------------------------------------------------
# Base URLs (in-network). The *.keinstein0.ch names resolve to the local
# Caddy container via Docker DNS aliases; service names resolve directly.
# ---------------------------------------------------------------------------
CADDY_MATRIX_URL = "http://matrix.keinstein0.ch"  # Matrix client + S2S vhost
CADDY_STATUS_URL = "http://status.keinstein0.ch"  # Gated status UI vhost
CADDY_WWW_URL = "http://www.keinstein0.ch"        # Homepage + /api/status vhost
GATEWAY_URL = "http://matrix-auth-gateway:5000"   # direct to the gateway
STATUS_API_URL = "http://status-api:5001"         # direct to the Status API
MOCK_URL = "http://tuwunel:8008"                  # direct to the mock homeserver

# Back-compat alias: most Caddy-fronted scenarios run through the www vhost.
CADDY_URL = CADDY_WWW_URL

# Cache TTL from .env.test (seconds). Tests wait this long + a buffer for
# the Status API cache to expire.
CACHE_TTL = int(os.environ.get("CACHE_TTL_SECONDS", "2"))

# Paths for INT-CMP-01/02, which shell out to `docker compose` (the runner
# mounts the repo read-only at /workspace and the Docker socket).
COMPOSE_FILE = os.environ.get("COMPOSE_FILE", "/workspace/docker-compose.yml")
ENV_FILE = os.environ.get("ENV_FILE", "/workspace/.env.test")
PROJECT_ROOT = os.path.dirname(COMPOSE_FILE)


def _wait_for(url, timeout=120, interval=2, expected_status=200, headers=None):
    """Poll a URL until it returns the expected status or timeout."""
    deadline = time.time() + timeout
    last_error = None
    while time.time() < deadline:
        try:
            resp = requests.get(url, timeout=5, allow_redirects=False, headers=headers)
            if resp.status_code == expected_status:
                return resp
        except requests.RequestException as exc:
            last_error = exc
        time.sleep(interval)
    raise TimeoutError(
        f"Timed out waiting for {url} (expected {expected_status}). Last error: {last_error}"
    )


@pytest.fixture(scope="session")
def stack():
    """Wait for the compose stack (started by the caller) to be ready."""
    _wait_for(f"{MOCK_URL}/_matrix/client/versions", timeout=120)
    _wait_for(f"{GATEWAY_URL}/healthz", timeout=120)
    _wait_for(f"{STATUS_API_URL}/healthz", timeout=120)
    # The matrix vhost serves client + S2S discovery; /login.html on www
    # depends on the homepage-build one-shot having populated static_build.
    _wait_for(f"{CADDY_MATRIX_URL}/.well-known/matrix/client", timeout=120)
    _wait_for(f"{CADDY_WWW_URL}/login.html", timeout=120)

    yield  # tests run here


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def login_via_gateway(username, password, redirect="/", room="status-viewers"):
    """POST /login to the auth gateway and return (response, cookie_value).

    Extracts the signed cookie value from the Set-Cookie header manually,
    because requests' session won't send a Secure cookie over plain HTTP.
    """
    resp = requests.post(
        f"{GATEWAY_URL}/login",
        data={"username": username, "password": password,
              "redirect": redirect, "room": room},
        allow_redirects=False,
        timeout=10,
    )
    cookie_value = None
    set_cookie = resp.headers.get("Set-Cookie", "")
    if "matrix_auth_session=" in set_cookie:
        # Extract the value between 'matrix_auth_session=' and the first ';'.
        raw = set_cookie.split("matrix_auth_session=", 1)[1]
        cookie_value = raw.split(";", 1)[0]
    return resp, cookie_value


def auth_headers(cookie_value):
    """Return a headers dict with the session cookie for manual injection."""
    return {"Cookie": f"matrix_auth_session={cookie_value}"}


def wait_for_cache_expiry(extra=1):
    """Sleep long enough for the Status API cache to expire."""
    time.sleep(CACHE_TTL + extra)


def mock_admin(action):
    """Call a /__admin/* endpoint on the mock and return the JSON response."""
    resp = requests.post(f"{MOCK_URL}/__admin/{action}", timeout=5)
    resp.raise_for_status()
    return resp.json()


def mock_stats():
    """Return the mock's request counts as a dict."""
    resp = requests.get(f"{MOCK_URL}/__admin/stats", timeout=5)
    resp.raise_for_status()
    return resp.json()

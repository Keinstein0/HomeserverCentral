"""
Integration test suite for HomeserverCentral (Phase 2 / TESTING.md §3).

Spins up the full containerized stack via Docker Compose under the `test`
profile, waits for all services to be healthy, then exercises the 18
end-to-end HTTP scenarios (INT-CAD-* through INT-CMP-*).

Run with:
    cd tests/integration
    pip install -r requirements.txt
    pytest -v

Set KEEP_STACK=1 to skip teardown after a run (useful for debugging):
    KEEP_STACK=1 pytest -v
"""

import os
import subprocess
import time

import pytest
import requests


# ---------------------------------------------------------------------------
# Base URLs (host-published ports, see docker-compose.yml)
# ---------------------------------------------------------------------------
CADDY_URL = "http://localhost:80"
GATEWAY_URL = "http://localhost:5000"
STATUS_API_URL = "http://localhost:5001"
MOCK_URL = "http://localhost:8008"

# Cache TTL from .env.test (seconds). Tests wait this long + a buffer for
# the Status API cache to expire.
CACHE_TTL = int(os.environ.get("CACHE_TTL_SECONDS", "2"))

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
COMPOSE_FILE = os.path.join(PROJECT_ROOT, "docker-compose.yml")
ENV_FILE = os.path.join(PROJECT_ROOT, ".env.test")


def _compose_cmd(*args):
    """Build a docker compose command for the test profile."""
    return [
        "docker", "compose",
        "--profile", "test",
        "--env-file", ENV_FILE,
        "-f", COMPOSE_FILE,
        *args,
    ]


def _wait_for(url, timeout=120, interval=2, expected_status=200):
    """Poll a URL until it returns the expected status or timeout."""
    deadline = time.time() + timeout
    last_error = None
    while time.time() < deadline:
        try:
            resp = requests.get(url, timeout=5, allow_redirects=False)
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
    """Start the full test stack, wait for health, yield, then tear down."""
    # Clean up any leftover containers from a previous run.
    subprocess.run(_compose_cmd("down", "-v"), capture_output=True, timeout=60)

    # Build and start.
    up_cmd = _compose_cmd("up", "-d", "--build")
    result = subprocess.run(up_cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        # Print logs to help diagnose.
        logs = subprocess.run(_compose_cmd("logs"), capture_output=True, text=True, timeout=30)
        raise RuntimeError(
            f"docker compose up failed (exit {result.returncode}):\n"
            f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}\nLOGS:\n{logs.stdout}"
        )

    # Wait for each service to be healthy (sequential, each has its own
    # timeout). The order matters: the mock must be up before the gateway
    # can serve logins, and the static build must complete before Caddy
    # can serve /login.html.
    _wait_for(f"{MOCK_URL}/_matrix/client/versions", timeout=120)
    _wait_for(f"{GATEWAY_URL}/healthz", timeout=120)
    _wait_for(f"{STATUS_API_URL}/healthz", timeout=120)
    _wait_for(f"{CADDY_URL}/_matrix/client/.well-known/matrix/client", timeout=120)
    # /login.html depends on the homepage-build one-shot having populated
    # the static_build volume.
    _wait_for(f"{CADDY_URL}/login.html", timeout=120)

    yield  # tests run here

    # Teardown unless KEEP_STACK is set.
    if os.environ.get("KEEP_STACK"):
        print("\n[KEEP_STACK=1] Skipping teardown. Run manually: "
              f"docker compose --profile test -f {COMPOSE_FILE} down -v")
    else:
        subprocess.run(_compose_cmd("down", "-v"), capture_output=True, timeout=60)


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

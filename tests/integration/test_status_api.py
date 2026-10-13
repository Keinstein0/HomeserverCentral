"""INT-STA-01 through INT-STA-06: Status API health, discovery, probes, cache, protected access."""

import requests

from conftest import (
    STATUS_API_URL, CADDY_URL, MOCK_URL,
    login_via_gateway, auth_headers,
    wait_for_cache_expiry, mock_admin, mock_stats,
)


# INT-STA-01: Service Self-Health
def test_int_sta_01_self_health(stack):
    resp = requests.get(f"{STATUS_API_URL}/healthz", timeout=10)
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "UP"


# INT-STA-02: Service Discovery
def test_int_sta_02_service_discovery(stack):
    resp = requests.get(f"{STATUS_API_URL}/services", timeout=10)
    assert resp.status_code == 200
    services = resp.json()
    ids = [s["id"] for s in services]
    for expected_id in ["auth-gateway", "tuwunel", "homepage", "caddy"]:
        assert expected_id in ids, f"Missing service: {expected_id}"


# INT-STA-03: Live Status Probe (Healthy)
def test_int_sta_03_live_probe_healthy(stack):
    for service_id in ["auth-gateway", "tuwunel"]:
        resp = requests.get(f"{STATUS_API_URL}/services/{service_id}", timeout=10)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "UP", f"{service_id} status: {data['status']}"
        assert data["response_time_ms"] >= 0


# INT-STA-04: Live Status Probe (Degraded/Down)
def test_int_sta_04_live_probe_down(stack):
    # First ensure tuwunel is UP (and cache is warm).
    resp = requests.get(f"{STATUS_API_URL}/services/tuwunel", timeout=10)
    assert resp.json()["status"] == "UP"

    # Simulate downstream failure on the mock.
    mock_admin("fail")

    # Wait for the Status API cache to expire.
    wait_for_cache_expiry()

    # Now the next probe should show DOWN or DEGRADED.
    resp = requests.get(f"{STATUS_API_URL}/services/tuwunel", timeout=10)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("DOWN", "DEGRADED"), f"Expected DOWN/DEGRADED, got {data['status']}"

    # Cleanup: recover the mock.
    mock_admin("recover")
    wait_for_cache_expiry()
    resp = requests.get(f"{STATUS_API_URL}/services/tuwunel", timeout=10)
    assert resp.json()["status"] == "UP"


# INT-STA-05: Cache Buffer & Burst Protection
def test_int_sta_05_cache_burst_protection(stack):
    # Ensure cache is expired so the next probe actually hits the downstream.
    wait_for_cache_expiry()
    mock_admin("reset_stats")

    # Send 10 concurrent requests to /services/tuwunel within the TTL window.
    import concurrent.futures

    urls = [f"{STATUS_API_URL}/services/tuwunel"] * 10
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(
            lambda: requests.get(u, timeout=10).json()
        ) for u in urls]
        results = [f.result() for f in futures]

    # All 10 responses must have the identical last_checked timestamp.
    timestamps = [r["last_checked"] for r in results]
    assert len(set(timestamps)) == 1, f"Expected identical timestamps, got: {set(timestamps)}"

    # The downstream service (mock's /_matrix/client/versions) must have been
    # pinged only once.
    stats = mock_stats()
    assert stats["versions"] == 1, f"Expected 1 versions call, got {stats['versions']}"


# INT-STA-06: Protected Status Access
def test_int_sta_06_protected_status_access(stack):
    # Without login cookie -> 302 redirect to /login.html.
    resp = requests.get(
        f"{CADDY_URL}/api/status/services",
        timeout=10,
        allow_redirects=False,
    )
    assert resp.status_code == 302
    assert resp.headers["Location"].startswith("/login.html")

    # With a valid session cookie (alice is a member of status-viewers).
    _, cookie = login_via_gateway("alice", "password")
    resp2 = requests.get(
        f"{CADDY_URL}/api/status/services",
        headers=auth_headers(cookie),
        timeout=10,
        allow_redirects=False,
    )
    assert resp2.status_code == 200
    data = resp2.json()
    # Should return the list of registered services.
    assert isinstance(data, list)
    assert len(data) > 0

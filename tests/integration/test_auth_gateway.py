"""INT-AUT-01 through INT-AUT-05: Auth Gateway health, login, membership, logout."""

import requests

from conftest import (
    GATEWAY_URL, CADDY_URL,
    login_via_gateway, auth_headers,
)


# INT-AUT-01: Gateway Self-Health
def test_int_aut_01_gateway_health(stack):
    resp = requests.get(f"{GATEWAY_URL}/healthz", timeout=10)
    assert resp.status_code == 200
    assert resp.text.strip() == "ok"


# INT-AUT-02: Valid Login Flow
def test_int_aut_02_valid_login(stack):
    resp, cookie_value = login_via_gateway("alice", "password")
    assert resp.status_code == 302
    # A signed session cookie must be issued.
    assert cookie_value is not None
    assert len(cookie_value) > 10
    # Cookie attributes.
    set_cookie = resp.headers.get("Set-Cookie", "")
    assert "HttpOnly" in set_cookie
    assert "matrix_auth_session=" in set_cookie


# INT-AUT-03: Invalid Credentials
def test_int_aut_03_invalid_credentials(stack):
    resp, cookie_value = login_via_gateway("alice", "wrong_password")
    assert resp.status_code == 302
    location = resp.headers["Location"]
    assert "error=invalid_credentials" in location
    assert location.startswith("/login.html")
    # No session cookie should be issued.
    assert cookie_value is None or "matrix_auth_session=" not in resp.headers.get("Set-Cookie", "")


# INT-AUT-04: Unauthorized Member (403)
def test_int_aut_04_unauthorized_member_403(stack):
    # Login as bob (valid credentials but NOT a member of status-viewers).
    _, bob_cookie = login_via_gateway("bob", "password")
    assert bob_cookie is not None

    # Access a protected route through Caddy with bob's session.
    resp = requests.get(
        f"{CADDY_URL}/api/status/services",
        headers=auth_headers(bob_cookie),
        timeout=10,
        allow_redirects=False,
    )
    # forward_auth returns 403 -> Caddy serves 403.html with 403 status.
    assert resp.status_code == 403
    # The 403 page content should be served.
    assert "403" in resp.text or "Access denied" in resp.text


# INT-AUT-05: Logout Flow
def test_int_aut_05_logout_flow(stack):
    # Login as alice.
    _, alice_cookie = login_via_gateway("alice", "password")
    assert alice_cookie is not None

    # Logout with the active session.
    logout_resp = requests.get(
        f"{GATEWAY_URL}/logout",
        headers=auth_headers(alice_cookie),
        timeout=10,
        allow_redirects=False,
    )
    assert logout_resp.status_code == 302
    assert logout_resp.headers["Location"].endswith("/login.html")
    # Cookie should be expired.
    set_cookie = logout_resp.headers.get("Set-Cookie", "")
    assert "Max-Age=0" in set_cookie or "max-age=0" in set_cookie.lower()

    # Subsequent protected request with the old cookie must redirect to login.
    resp2 = requests.get(
        f"{CADDY_URL}/api/status/services",
        headers=auth_headers(alice_cookie),
        timeout=10,
        allow_redirects=False,
    )
    assert resp2.status_code == 302
    assert resp2.headers["Location"].startswith("/login.html")

"""INT-CAD-01 through INT-CAD-04: Caddy ingress, static assets, auth redirect, headers."""

import pytest
import requests

from conftest import CADDY_URL


# INT-CAD-01: Ingress & Startup Health
def test_int_cad_01_ingress_startup(stack):
    resp = requests.get(
        f"{CADDY_URL}/_matrix/client/.well-known/matrix/client",
        timeout=10,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "m.homeserver" in data
    assert "base_url" in data["m.homeserver"]


# INT-CAD-02: Public Static Assets (no forward_auth redirect)
def test_int_cad_02_public_static_assets(stack):
    for path in ["/login.html", "/assets/style.css"]:
        resp = requests.get(f"{CADDY_URL}{path}", timeout=10, allow_redirects=False)
        assert resp.status_code == 200, f"{path} returned {resp.status_code}"
        # Must NOT be a redirect to /login.html.
        assert resp.status_code != 302

    # login.html should contain a form.
    login_resp = requests.get(f"{CADDY_URL}/login.html", timeout=10)
    assert "<form" in login_resp.text.lower()


# INT-CAD-03: Forward Auth Redirection (protected route without session)
def test_int_cad_03_forward_auth_redirect(stack):
    resp = requests.get(
        f"{CADDY_URL}/api/status/services",
        timeout=10,
        allow_redirects=False,
    )
    assert resp.status_code == 302
    location = resp.headers["Location"]
    assert location.startswith("/login.html?redirect=")
    assert "room=status-viewers" in location


# INT-CAD-04: Header Security
def test_int_cad_04_header_security(stack):
    resp = requests.get(f"{CADDY_URL}/login.html", timeout=10)
    assert resp.headers.get("X-Frame-Options") == "DENY"
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    # Server header should be stripped (-Server directive).
    assert "Server" not in resp.headers or resp.headers.get("Server", "") == ""

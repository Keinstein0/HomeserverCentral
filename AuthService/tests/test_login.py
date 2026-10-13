"""Tests for the POST /login route and user-id normalization."""

from urllib.parse import quote

import pytest
import responses

import app


# ---------------------------------------------------------------------------
# normalize_user_id
# ---------------------------------------------------------------------------

def test_normalize_user_id_bare_name_expands():
    assert app.normalize_user_id("alice") == "@alice:keinstein0.ch"


def test_normalize_user_id_full_id_passthrough():
    assert app.normalize_user_id("@alice:matrix.example.com") == "@alice:matrix.example.com"


def test_normalize_user_id_no_server_name_passthrough(monkeypatch):
    monkeypatch.setattr(app, "DEFAULT_SERVER_NAME", None)
    assert app.normalize_user_id("alice") == "alice"


# ---------------------------------------------------------------------------
# POST /login
# ---------------------------------------------------------------------------

LOGIN_URL = "http://tuwunel:8008/_matrix/client/v3/login"


@responses.activate
def test_login_success_sets_cookie_and_redirects(client):
    responses.add(
        responses.POST,
        LOGIN_URL,
        status=200,
        json={
            "user_id": "@alice:keinstein0.ch",
            "access_token": "tok_alice",
            "home_server": "keinstein0.ch",
        },
    )

    resp = client.post(
        "/login",
        data={
            "username": "alice",
            "password": "password",
            "redirect": "/dashboard",
            "room": "status-viewers",
        },
    )

    assert resp.status_code == 302
    assert resp.headers["Location"] == "/dashboard"

    # A signed session cookie must be issued with the right attributes.
    cookie_header = resp.headers.get("Set-Cookie", "")
    assert "matrix_auth_session=" in cookie_header
    assert "HttpOnly" in cookie_header
    assert "SameSite=Lax" in cookie_header
    assert "Secure" in cookie_header
    # A session must have been stored server-side.
    assert len(app.SESSIONS) == 1
    assert app.SESSIONS[next(iter(app.SESSIONS))]["user_id"] == "@alice:keinstein0.ch"


@responses.activate
def test_login_invalid_credentials_redirects_to_error(client):
    responses.add(
        responses.POST,
        LOGIN_URL,
        status=403,
        json={"errcode": "M_FORBIDDEN", "error": "Invalid username or password"},
    )

    resp = client.post(
        "/login",
        data={
            "username": "alice",
            "password": "wrong",
            "redirect": "/dashboard",
            "room": "status-viewers",
        },
    )

    assert resp.status_code == 302
    location = resp.headers["Location"]
    assert location.startswith("/login.html?")
    assert "error=invalid_credentials" in location
    assert f"redirect={quote('/dashboard', safe='')}" in location
    assert f"room={quote('status-viewers', safe='')}" in location
    # No session issued on failure.
    assert app.SESSIONS == {}


def test_login_missing_fields_redirects_to_error(client):
    resp = client.post(
        "/login",
        data={"username": "", "password": "", "redirect": "/dashboard", "room": "status-viewers"},
    )
    assert resp.status_code == 302
    location = resp.headers["Location"]
    assert location.startswith("/login.html?")
    assert "error=missing_fields" in location
    assert app.SESSIONS == {}


def test_login_missing_fields_when_only_username(client):
    resp = client.post(
        "/login",
        data={"username": "alice", "password": "", "redirect": "/", "room": ""},
    )
    assert resp.status_code == 302
    assert "error=missing_fields" in resp.headers["Location"]


@responses.activate
def test_login_homeserver_network_error_redirects_to_error(client, monkeypatch):
    """A network exception talking to the homeserver must not crash; it is
    treated as a failed login and the user is sent back to the login page."""
    import requests as req

    def boom(*args, **kwargs):
        raise req.RequestException("connection refused")

    monkeypatch.setattr(req, "post", boom)

    resp = client.post(
        "/login",
        data={"username": "alice", "password": "password", "redirect": "/", "room": ""},
    )
    assert resp.status_code == 302
    assert "error=invalid_credentials" in resp.headers["Location"]
    assert app.SESSIONS == {}


@responses.activate
def test_login_default_redirect_when_none_given(client):
    responses.add(
        responses.POST, LOGIN_URL, status=200,
        json={"user_id": "@alice:keinstein0.ch", "access_token": "tok"},
    )
    resp = client.post("/login", data={"username": "alice", "password": "password"})
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/"

"""Tests for session cookie generation, cryptographic signing, and expiration."""

import pytest
import responses

import app
from conftest import make_session_cookie


LOGIN_URL = "http://tuwunel:8008/_matrix/client/v3/login"


def test_cookie_roundtrips_to_session(client):
    """A cookie issued by /login decodes to a session_id that exists in the
    server-side SESSIONS store."""
    with responses.RequestsMock() as rsps:
        rsps.add(
            responses.POST, LOGIN_URL, status=200,
            json={"user_id": "@alice:keinstein0.ch", "access_token": "tok"},
        )
        resp = client.post("/login", data={"username": "alice", "password": "password", "redirect": "/"})

    set_cookie = resp.headers["Set-Cookie"]
    # Extract just the cookie value (before the first ';').
    cookie_value = set_cookie.split(";", 1)[0]
    name, _, signed = cookie_value.partition("=")
    assert name == "matrix_auth_session"
    # Decoding the signed value must yield a real session id.
    session_id = app.serializer.loads(signed, max_age=app.SESSION_MAX_AGE)
    assert session_id in app.SESSIONS
    assert app.SESSIONS[session_id]["user_id"] == "@alice:keinstein0.ch"


def test_cookie_tampered_rejected(client):
    cookie, _ = make_session_cookie(client)
    tampered = ("X" + cookie[1:]) if cookie[0] != "X" else ("Y" + cookie[1:])
    client.set_cookie(app.COOKIE_NAME, tampered)
    resp = client.get("/verify")
    assert resp.status_code == 401


def test_cookie_expired_rejected(client, monkeypatch):
    """A cookie validated with a negative max_age is immediately expired."""
    cookie, session_id = make_session_cookie(client)
    assert session_id in app.SESSIONS  # session exists
    # itsdangerous treats max_age=0 as "no max age" (unlimited), so use -1
    # to force immediate SignatureExpired.
    monkeypatch.setattr(app, "SESSION_MAX_AGE", -1)
    resp = client.get("/verify")
    assert resp.status_code == 401


def test_logout_clears_session(client):
    cookie, session_id = make_session_cookie(client)
    assert session_id in app.SESSIONS

    resp = client.get("/logout")
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/login.html")
    # Session removed.
    assert session_id not in app.SESSIONS
    # The Set-Cookie expires the cookie.
    set_cookie = resp.headers.get("Set-Cookie", "")
    assert "matrix_auth_session=" in set_cookie
    assert "Max-Age=0" in set_cookie or "expires=0" in set_cookie.lower() or "Max-Age=0" in set_cookie

    # Subsequent protected request must be rejected.
    resp2 = client.get("/verify")
    assert resp2.status_code == 401


def test_logout_with_no_cookie_still_redirects(client):
    resp = client.get("/logout")
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/login.html")


@responses.activate
def test_cookie_security_attributes(client):
    responses.add(
        responses.POST, LOGIN_URL, status=200,
        json={"user_id": "@alice:keinstein0.ch", "access_token": "tok"},
    )
    resp = client.post("/login", data={"username": "alice", "password": "password", "redirect": "/"})
    set_cookie = resp.headers["Set-Cookie"]
    assert "HttpOnly" in set_cookie
    assert "SameSite=Lax" in set_cookie
    assert "Secure" in set_cookie

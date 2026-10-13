"""Tests for the GET /verify authorization route (the core of the gateway)."""

from urllib.parse import quote

import pytest
import responses

import app
from conftest import make_session_cookie


HOMESERVER = "http://tuwunel:8008"
ALIAS_URL = f"{HOMESERVER}/_matrix/client/v3/directory/room/{quote('#status-viewers:keinstein0.ch', safe='')}"
ROOM_ID = "!statusroom:keinstein0.ch"
JOINED_URL = f"{HOMESERVER}/_matrix/client/v3/rooms/{quote(ROOM_ID, safe='')}/joined_members"
POWER_URL = f"{HOMESERVER}/_matrix/client/v3/rooms/{quote(ROOM_ID, safe='')}/state/m.room.power_levels"


def _member_responses():
    """Register the standard happy-path homeserver responses for a member."""
    responses.add(responses.GET, ALIAS_URL, status=200, json={"room_id": ROOM_ID})
    responses.add(
        responses.GET, JOINED_URL, status=200,
        json={"joined": {"@alice:keinstein0.ch": {"display_name": "alice"}}},
    )
    responses.add(
        responses.GET, POWER_URL, status=200,
        json={"users_default": 0, "users": {"@alice:keinstein0.ch": 50}},
    )


# ---------------------------------------------------------------------------
# Authentication (cookie) failures
# ---------------------------------------------------------------------------

def test_verify_no_cookie_401(client):
    assert client.get("/verify?room=status-viewers").status_code == 401


def test_verify_tampered_cookie_401(client):
    cookie, _ = make_session_cookie(client)
    tampered = ("X" + cookie[1:]) if cookie[0] != "X" else ("Y" + cookie[1:])
    # Overwrite the valid cookie in the jar with a tampered value.
    client.set_cookie(app.COOKIE_NAME, tampered)
    resp = client.get("/verify?room=status-viewers")
    assert resp.status_code == 401


def test_verify_unknown_session_401(client):
    """A validly signed cookie whose session isn't in the in-memory store
    (e.g. gateway restarted) must force re-login."""
    bogus_cookie = app.serializer.dumps("nonexistent-session-id")
    client.set_cookie(app.COOKIE_NAME, bogus_cookie)
    resp = client.get("/verify?room=status-viewers")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Logged-in, no room argument
# ---------------------------------------------------------------------------

def test_verify_no_room_arg_200_when_logged_in(client):
    cookie, _ = make_session_cookie(client)
    resp = client.get("/verify")
    assert resp.status_code == 200
    assert resp.headers.get("X-Auth-User") == "@alice:keinstein0.ch"
    # No homeserver calls should have been made.
    assert len(responses.calls) == 0


# ---------------------------------------------------------------------------
# Room membership checks (homeserver mocked)
# ---------------------------------------------------------------------------

@responses.activate
def test_verify_member_200_with_headers(client):
    _member_responses()
    cookie, _ = make_session_cookie(client, user_id="@alice:keinstein0.ch")
    resp = client.get("/verify?room=status-viewers")
    assert resp.status_code == 200
    assert resp.headers.get("X-Auth-User") == "@alice:keinstein0.ch"
    assert resp.headers.get("X-Auth-Power-Level") == "50"


@responses.activate
def test_verify_non_member_403(client):
    responses.add(responses.GET, ALIAS_URL, status=200, json={"room_id": ROOM_ID})
    responses.add(
        responses.GET, JOINED_URL, status=200,
        json={"joined": {"@someoneelse:keinstein0.ch": {"display_name": "x"}}},
    )
    cookie, _ = make_session_cookie(client, user_id="@bob:keinstein0.ch")
    resp = client.get("/verify?room=status-viewers")
    assert resp.status_code == 403


@responses.activate
def test_verify_room_alias_resolution_failure_403(client):
    responses.add(responses.GET, ALIAS_URL, status=404, json={"errcode": "M_NOT_FOUND"})
    cookie, _ = make_session_cookie(client)
    resp = client.get("/verify?room=status-viewers")
    assert resp.status_code == 403


@responses.activate
def test_verify_bot_not_joined_403(client):
    responses.add(responses.GET, ALIAS_URL, status=200, json={"room_id": ROOM_ID})
    responses.add(responses.GET, JOINED_URL, status=403, json={"errcode": "M_FORBIDDEN"})
    cookie, _ = make_session_cookie(client)
    resp = client.get("/verify?room=status-viewers")
    assert resp.status_code == 403


@responses.activate
def test_verify_alias_resolution_cached(client):
    _member_responses()
    cookie, _ = make_session_cookie(client)
    r1 = client.get("/verify?room=status-viewers")
    r2 = client.get("/verify?room=status-viewers")
    assert r1.status_code == 200 and r2.status_code == 200
    alias_calls = [c for c in responses.calls if c.request.url == ALIAS_URL]
    assert len(alias_calls) == 1


@responses.activate
def test_verify_raw_room_id_passthrough(client):
    responses.add(
        responses.GET,
        f"{HOMESERVER}/_matrix/client/v3/rooms/{quote(ROOM_ID, safe='')}/joined_members",
        status=200, json={"joined": {"@alice:keinstein0.ch": {}}},
    )
    responses.add(
        responses.GET,
        f"{HOMESERVER}/_matrix/client/v3/rooms/{quote(ROOM_ID, safe='')}/state/m.room.power_levels",
        status=200, json={"users_default": 0, "users": {"@alice:keinstein0.ch": 0}},
    )
    cookie, _ = make_session_cookie(client)
    resp = client.get(f"/verify?room={quote(ROOM_ID, safe='')}")
    assert resp.status_code == 200
    assert all(c.request.url != ALIAS_URL for c in responses.calls)


def test_verify_malformed_bare_room_without_server_name_403(client, monkeypatch):
    monkeypatch.setattr(app, "DEFAULT_SERVER_NAME", None)
    cookie, _ = make_session_cookie(client)
    resp = client.get("/verify?room=just-a-name")
    assert resp.status_code == 403


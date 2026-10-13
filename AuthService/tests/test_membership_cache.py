"""Tests for the room-membership cache and eviction behavior."""

from urllib.parse import quote

import responses

import app
from conftest import make_session_cookie

HOMESERVER = "http://tuwunel:8008"
ALIAS = "#status-viewers:keinstein0.ch"
ROOM_ID = "!statusroom:keinstein0.ch"
ALIAS_URL = f"{HOMESERVER}/_matrix/client/v3/directory/room/{quote(ALIAS, safe='')}"
JOINED_URL = (
    f"{HOMESERVER}/_matrix/client/v3/rooms/{quote(ROOM_ID, safe='')}/joined_members"
)
POWER_URL = (
    f"{HOMESERVER}/_matrix/client/v3/rooms/{quote(ROOM_ID, safe='')}"
    "/state/m.room.power_levels"
)


def _register_homeserver():
    responses.add(responses.GET, ALIAS_URL, status=200, json={"room_id": ROOM_ID})
    responses.add(
        responses.GET,
        JOINED_URL,
        status=200,
        json={"joined": {"@alice:keinstein0.ch": {"display_name": "alice"}}},
    )
    responses.add(
        responses.GET,
        POWER_URL,
        status=200,
        json={"users_default": 0, "users": {"@alice:keinstein0.ch": 50}},
    )


@responses.activate
def test_membership_cached_within_ttl(client):
    _register_homeserver()
    cookie, _ = make_session_cookie(client, user_id="@alice:keinstein0.ch")

    r1 = client.get("/verify?room=status-viewers")
    r2 = client.get("/verify?room=status-viewers")

    assert r1.status_code == 200 and r2.status_code == 200
    # joined_members should have been hit exactly once (cached on the second call).
    joined_calls = [c for c in responses.calls if c.request.url == JOINED_URL]
    assert len(joined_calls) == 1


@responses.activate
def test_membership_refetched_after_ttl(client, monkeypatch):
    _register_homeserver()
    cookie, _ = make_session_cookie(client, user_id="@alice:keinstein0.ch")

    # Use a tiny TTL so the cache expires immediately between calls.
    monkeypatch.setattr(app, "MEMBERSHIP_CACHE_TTL", 0)

    client.get("/verify?room=status-viewers")
    client.get("/verify?room=status-viewers")

    joined_calls = [c for c in responses.calls if c.request.url == JOINED_URL]
    # With TTL 0, every verify must re-fetch membership.
    assert len(joined_calls) == 2


@responses.activate
def test_cache_keyed_per_session_and_room(client):
    _register_homeserver()
    # Two distinct sessions (both in SESSIONS); the cookie jar holds one
    # cookie at a time, so we set alice's, request, then overwrite with
    # bob's and request again. Different session_ids -> different cache
    # keys -> two joined_members calls.
    cookie_a, _ = make_session_cookie(client, user_id="@alice:keinstein0.ch")
    client.get("/verify?room=status-viewers")

    cookie_b, _ = make_session_cookie(client, user_id="@bob:keinstein0.ch")
    client.get("/verify?room=status-viewers")

    joined_calls = [c for c in responses.calls if c.request.url == JOINED_URL]
    assert len(joined_calls) == 2

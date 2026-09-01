"""
matrix-auth-gateway
--------------------
A minimal replacement for oauth2-proxy that authenticates users against a
Matrix homeserver (tuwunel/Synapse) and checks room membership using a
plain, unprivileged bot account, then exposes a /verify endpoint that
Caddy's forward_auth directive can call.

No admin token, no OIDC, no matrix-user-verification-service involved.
The bot only ever sees membership of rooms it has itself been invited
into and joined - it cannot read or affect anything else on the server.

Flow:
  1. POST /login          -> log in against the homeserver, store a
                              server-side session keyed by a random id,
                              set a signed cookie, then 302-redirect back
                              to `redirect` (or to /login.html?error=1&...
                              on failure). The actual login FORM is a
                              static page served by Caddy, not this app -
                              this endpoint is a pure headless API/redirect
                              target.
  2. GET  /verify?room=X  -> called by Caddy on every request to a
                              protected path. Validates the cookie, then
                              (with short-lived caching) asks the bot
                              account to list room X's joined members and
                              checks whether the session's user is in it.
  3. GET  /logout         -> clear the session, redirect to /login.html

Env vars (see docker-compose.snippet.yml):
  HOMESERVER_URL       e.g. http://tuwunel:8008
  BOT_ACCESS_TOKEN     access token for a plain bot account that has been
                       invited into and joined every gated room
  GATEWAY_SECRET_KEY   required, random long string, signs the session cookie
  MATRIX_SERVER_NAME   optional, used to expand bare usernames to @user:server
  SESSION_MAX_AGE      seconds, default 7 days
  MEMBERSHIP_CACHE_TTL seconds, default 60 - avoids hitting the homeserver
                       on every single asset request
"""

import logging
import os
import secrets
import time
from urllib.parse import quote

import requests
from flask import Flask, make_response, redirect, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("matrix-auth-gateway")

app = Flask(__name__)

HOMESERVER_URL = os.environ.get("HOMESERVER_URL", "http://tuwunel:8008").rstrip("/")
BOT_ACCESS_TOKEN = os.environ["BOT_ACCESS_TOKEN"]  # required - fail fast if missing
DEFAULT_SERVER_NAME = os.environ.get("MATRIX_SERVER_NAME")  # used to expand bare room/user names

SECRET_KEY = os.environ["GATEWAY_SECRET_KEY"]  # required - fail fast if missing
SESSION_MAX_AGE = int(os.environ.get("SESSION_MAX_AGE", 60 * 60 * 24 * 7))  # 7 days
MEMBERSHIP_CACHE_TTL = int(os.environ.get("MEMBERSHIP_CACHE_TTL", 60))

COOKIE_NAME = "matrix_auth_session"
serializer = URLSafeTimedSerializer(SECRET_KEY, salt="matrix-auth-gateway")

# In-memory server-side session + membership caches.
# Fine for a single-instance homelab deployment; lost on restart (users
# just log in again). Swap for Redis if you ever run >1 replica.
SESSIONS: dict[str, dict] = {}
MEMBERSHIP_CACHE: dict[tuple[str, str], tuple[float, bool, int]] = {}
# alias/name -> resolved room id (!...). Aliases essentially never change,
# so this is cached indefinitely rather than on the short membership TTL.
ALIAS_CACHE: dict[str, str] = {}

def normalize_user_id(username: str) -> str:
    if username.startswith("@"):
        return username
    if not DEFAULT_SERVER_NAME:
        # If they didn't type a full @user:server id and we don't have a
        # default server configured, just pass through - the homeserver
        # login call will fail cleanly with a bad-request/unknown user.
        return username
    return f"@{username}:{DEFAULT_SERVER_NAME}"


def matrix_login(user_id: str, password: str) -> tuple[str, str] | None:
    """Log in against the homeserver. Returns (access_token, canonical_user_id) or None."""
    try:
        resp = requests.post(
            f"{HOMESERVER_URL}/_matrix/client/v3/login",
            json={
                "type": "m.login.password",
                "identifier": {"type": "m.id.user", "user": user_id},
                "password": password,
            },
            timeout=10,
        )
    except requests.RequestException:
        log.exception("Homeserver login request failed")
        return None
    if resp.status_code != 200:
        log.info("Login failed for %s: %s %s", user_id, resp.status_code, resp.text[:200])
        return None
    data = resp.json()
    return data.get("access_token"), data.get("user_id", user_id)


def resolve_room_id(room_param: str) -> str | None:
    """
    Accepts, in order of preference for readability:
      - a bare room name, e.g. "test-service"  -> expanded to
        "#test-service:{MATRIX_SERVER_NAME}"
      - a full alias, e.g. "#test-service:matrix.keinstein0.ch"
      - a raw room ID, e.g. "!aBcDefGHijK1234567:matrix.keinstein0.ch"
        (passed through unchanged, no lookup needed)

    Resolution goes through the standard room directory endpoint, using
    the bot's own token. Requires the room to have a PUBLISHED alias set
    in its room settings - a display name alone is not an alias.
    """
    if room_param.startswith("!"):
        return room_param

    if room_param.startswith("#"):
        alias = room_param
    else:
        if not DEFAULT_SERVER_NAME:
            log.warning(
                "Bare room name '%s' given but MATRIX_SERVER_NAME isn't set - "
                "can't expand it to a full alias", room_param,
            )
            return None
        alias = f"#{room_param}:{DEFAULT_SERVER_NAME}"

    if alias in ALIAS_CACHE:
        return ALIAS_CACHE[alias]

    try:
        resp = requests.get(
            f"{HOMESERVER_URL}/_matrix/client/v3/directory/room/{quote(alias, safe='')}",
            headers={"Authorization": f"Bearer {BOT_ACCESS_TOKEN}"},
            timeout=10,
        )
    except requests.RequestException:
        log.exception("Room alias resolution failed for %s", alias)
        return None
    if resp.status_code != 200:
        log.warning(
            "Could not resolve alias %s (does the room have this alias published "
            "in its settings?): %s %s", alias, resp.status_code, resp.text[:200],
        )
        return None

    room_id = resp.json().get("room_id")
    if room_id:
        ALIAS_CACHE[alias] = room_id
    return room_id


def get_room_power_levels(room_id: str) -> dict:
    """Fetch the room's m.room.power_levels state event. Any joined member
    (including our bot) can read this - it's not a privileged call."""
    try:
        resp = requests.get(
            f"{HOMESERVER_URL}/_matrix/client/v3/rooms/{quote(room_id, safe='')}"
            f"/state/m.room.power_levels",
            headers={"Authorization": f"Bearer {BOT_ACCESS_TOKEN}"},
            timeout=10,
        )
    except requests.RequestException:
        log.exception("power_levels request failed")
        return {}
    if resp.status_code != 200:
        log.warning(
            "power_levels lookup failed for %s: %s %s", room_id, resp.status_code, resp.text[:300]
        )
        return {}
    return resp.json()


def bot_check_room_membership(room_param: str, user_id: str) -> tuple[bool, int]:
    """
    Ask the homeserver (as the unprivileged bot account) who's currently
    joined to the room referred to by room_param (name/alias/id), and
    whether user_id is among them. If so, also return their power level
    in that room (0 if unset/not applicable).

    This is the plain Client-Server API endpoint every Matrix client uses
    to render a member list - it requires the CALLER (the bot) to be
    joined to the room, nothing more. No admin token involved, and the
    bot can only ever answer for rooms it has itself been invited into.
    """
    room_id = resolve_room_id(room_param)
    if not room_id:
        return False, 0

    try:
        resp = requests.get(
            f"{HOMESERVER_URL}/_matrix/client/v3/rooms/{quote(room_id, safe='')}/joined_members",
            headers={"Authorization": f"Bearer {BOT_ACCESS_TOKEN}"},
            timeout=10,
        )
    except requests.RequestException:
        log.exception("joined_members request failed")
        return False, 0
    if resp.status_code != 200:
        # Most common cause: the bot itself isn't a member of this room yet.
        log.warning(
            "joined_members lookup failed for %s (bot may not be joined to this room): %s %s",
            room_id, resp.status_code, resp.text[:300],
        )
        return False, 0
    joined = resp.json().get("joined", {})
    if user_id not in joined:
        log.info("%s is not a member of %s (%s)", user_id, room_param, room_id)
        return False, 0

    pl_event = get_room_power_levels(room_id)
    users_default = pl_event.get("users_default", 0)
    power_level = pl_event.get("users", {}).get(user_id, users_default)
    return True, power_level


@app.route("/login", methods=["POST"])
def login_post():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    redirect_to = request.form.get("redirect") or "/"
    room = request.form.get("room", "")

    def back_to_login_with_error(error_code: str, status: int):
        # No HTML here - just bounce back to the static /login.html with
        # enough in the query string for its own JS to re-show the form,
        # prefilled, with an error message.
        qs = f"error={error_code}&redirect={quote(redirect_to, safe='')}&room={quote(room, safe='')}"
        return redirect(f"/login.html?{qs}")


    if not username or not password:
        return back_to_login_with_error("missing_fields", 400)

    user_id_attempt = normalize_user_id(username)
    result = matrix_login(user_id_attempt, password)
    if not result:
        return back_to_login_with_error("invalid_credentials", 401)

    access_token, canonical_user_id = result
    session_id = secrets.token_urlsafe(32)
    SESSIONS[session_id] = {
        "user_id": canonical_user_id,
        "access_token": access_token,
        "created_at": time.time(),
    }
    log.info("Login OK for %s", canonical_user_id)

    resp = make_response(redirect(redirect_to))
    signed = serializer.dumps(session_id)
    resp.set_cookie(
        COOKIE_NAME,
        signed,
        max_age=SESSION_MAX_AGE,
        httponly=True,
        secure=True,
        samesite="Lax",
    )
    return resp


@app.route("/logout")
def logout():
    cookie = request.cookies.get(COOKIE_NAME)
    if cookie:
        try:
            session_id = serializer.loads(cookie, max_age=SESSION_MAX_AGE)
            SESSIONS.pop(session_id, None)
        except (BadSignature, SignatureExpired):
            pass
    resp = make_response(redirect("/login.html"))
    resp.delete_cookie(COOKIE_NAME)
    return resp


@app.route("/verify")
def verify():
    room_id = request.args.get("room", "")

    cookie = request.cookies.get(COOKIE_NAME)
    if not cookie:
        return "no session", 401
    try:
        session_id = serializer.loads(cookie, max_age=SESSION_MAX_AGE)
    except (SignatureExpired, BadSignature):
        return "invalid or expired session", 401

    session = SESSIONS.get(session_id)
    if not session:
        # Cookie is validly signed but the gateway restarted (in-memory
        # store lost) or the session was never created. Force re-login.
        return "unknown session", 401

    if not room_id:
        # Route imported matrix_gate without a room argument: being logged
        # in at all is sufficient.
        resp = make_response("ok", 200)
        resp.headers["X-Auth-User"] = session["user_id"]
        return resp

    cache_key = (session_id, room_id)
    cached = MEMBERSHIP_CACHE.get(cache_key)
    now = time.time()
    if cached and now - cached[0] < MEMBERSHIP_CACHE_TTL:
        _, allowed, power_level = cached
    else:
        allowed, power_level = bot_check_room_membership(room_id, session["user_id"])
        MEMBERSHIP_CACHE[cache_key] = (now, allowed, power_level)

    if not allowed:
        return "not a member of the required room", 403

    resp = make_response("ok", 200)
    resp.headers["X-Auth-User"] = session["user_id"]
    resp.headers["X-Auth-Power-Level"] = str(power_level)
    return resp


@app.route("/healthz")
def healthz():
    return "ok", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

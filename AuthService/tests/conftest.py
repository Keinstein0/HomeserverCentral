"""
Shared pytest fixtures and configuration for the AuthService test suite.

The Auth Service (app.py) reads required environment variables at *import
time* and fails fast if they are missing, so this module sets deterministic
dummy values (matching the project-wide .env.test) before `app` is imported
by any test module. It also provides a Flask test client and resets the
module-global in-memory state between tests.
"""

import os

# --- Required env vars MUST be set before importing `app`. ---------------
# Use the same dummy values as the repo's .env.test so tests and the
# test/dev container stack share one consistent identity.
os.environ.setdefault("BOT_ACCESS_TOKEN", "test_bot_token_abcde")
os.environ.setdefault("GATEWAY_SECRET_KEY", "test_secret_key_12345")
os.environ.setdefault("HOMESERVER_URL", "http://tuwunel:8008")
os.environ.setdefault("MATRIX_SERVER_NAME", "keinstein0.ch")
os.environ.setdefault("MEMBERSHIP_CACHE_TTL", "60")
os.environ.setdefault("SESSION_MAX_AGE", "604800")

import pytest

import app


@pytest.fixture
def client():
    """A Flask test client (no real network socket is opened)."""
    return app.app.test_client()


@pytest.fixture(autouse=True)
def reset_state():
    """Clear in-memory session / membership / alias caches between tests so
    they cannot leak state into one another."""
    app.SESSIONS.clear()
    app.MEMBERSHIP_CACHE.clear()
    app.ALIAS_CACHE.clear()
    yield
    # Also clear after the test, in case a test leaves state behind.
    app.SESSIONS.clear()
    app.MEMBERSHIP_CACHE.clear()
    app.ALIAS_CACHE.clear()


def make_session_cookie(client, user_id="@alice:keinstein0.ch", access_token="mock_token"):
    """Inject a server-side session, set a valid signed cookie on the Flask
    test client's cookie jar, and return (cookie_value, session_id).

    Cookies must be set via the test client's cookie jar (not via the
    ``Cookie`` header) because Werkzeug's test client does not parse cookies
    from manually supplied request headers. The cookie is set WITHOUT the
    ``Secure`` attribute so the test client (which speaks plain HTTP) will
    actually send it.
    """
    import secrets
    import time

    session_id = secrets.token_urlsafe(32)
    app.SESSIONS[session_id] = {
        "user_id": user_id,
        "access_token": access_token,
        "created_at": time.time(),
    }
    signed = app.serializer.dumps(session_id)
    client.set_cookie(app.COOKIE_NAME, signed)
    return signed, session_id

"""INT-HOM-01: Static build delivery through Caddy."""

import requests

from conftest import CADDY_URL


# INT-HOM-01: Static Build Delivery
def test_int_hom_01_static_build_delivery(stack):
    # index.html (or the fallback) should be served as text/html.
    resp = requests.get(f"{CADDY_URL}/", timeout=10)
    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("Content-Type", "")

    # CSS should have the correct MIME type.
    css_resp = requests.get(f"{CADDY_URL}/assets/style.css", timeout=10)
    assert css_resp.status_code == 200
    assert "text/css" in css_resp.headers.get("Content-Type", "")

    # The extracted loginForm.js module should be served as JavaScript.
    js_resp = requests.get(f"{CADDY_URL}/lib/loginForm.js", timeout=10)
    assert js_resp.status_code == 200
    content_type = js_resp.headers.get("Content-Type", "")
    assert "javascript" in content_type, f"Expected JS mime, got: {content_type}"

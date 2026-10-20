"""Tests for the GET /healthz self-health endpoint."""


def test_healthz_200_ok(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.data == b"ok"

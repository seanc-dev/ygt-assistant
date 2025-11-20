from fastapi.testclient import TestClient
from presentation.api.app import app


def test_ms_oauth_start_redirects(monkeypatch):
    monkeypatch.setenv("MS_CLIENT_ID", "cid")
    monkeypatch.setenv("MS_CLIENT_SECRET", "secret")
    monkeypatch.setenv("MS_REDIRECT_URI", "https://example.com/callback")

    client = TestClient(app)
    resp = client.get(
        "/connections/ms/oauth/start",
        params={"tenant": "common", "user_id": "user"},
        follow_redirects=False,
    )

    assert resp.status_code == 302
    assert "login.microsoftonline.com" in resp.headers.get("location", "")


def test_ms_status_exposes_disconnect(monkeypatch):
    monkeypatch.setenv("MS_CLIENT_ID", "cid")
    monkeypatch.setenv("MS_CLIENT_SECRET", "secret")
    monkeypatch.setenv("MS_REDIRECT_URI", "https://example.com/callback")

    client = TestClient(app)
    resp = client.get("/connections/ms/status", params={"user_id": "user"})

    assert resp.status_code == 200
    assert resp.json()["connected"] is False

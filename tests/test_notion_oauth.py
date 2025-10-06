from fastapi.testclient import TestClient
import presentation.api.app as app_module
from presentation.api.app import app


def test_notion_start_redirect():
    client = TestClient(app)
    resp = client.get("/oauth/notion/start")
    # TestClient follows redirects; check status and location via no-follow
    resp = client.get("/oauth/notion/start", follow_redirects=False)
    assert resp.status_code == 302
    assert "api.notion.com/v1/oauth/authorize" in resp.headers["location"]
    assert "client_id=" in resp.headers["location"]
    assert "response_type=code" in resp.headers["location"]


def test_notion_callback_invalid_state():
    client = TestClient(app)
    resp = client.get(
        "/oauth/notion/callback", params={"code": "abc", "state": "bogus"}
    )
    assert resp.status_code == 400


def test_notion_callback_mock_flow(monkeypatch):
    monkeypatch.setattr(app_module, "MOCK_OAUTH", True)
    client = TestClient(app)
    # start to get state
    start = client.get("/oauth/notion/start", follow_redirects=False)
    assert start.status_code == 302
    # extract state from redirect url
    from urllib.parse import urlparse, parse_qs

    qs = parse_qs(urlparse(start.headers["location"]).query)
    state = qs["state"][0]

    # callback
    cb = client.get(
        "/oauth/notion/callback",
        params={"code": "abc", "state": state},
        follow_redirects=False,
    )
    assert cb.status_code == 302
    assert "/oauth/success" in cb.headers["location"]

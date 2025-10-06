from fastapi.testclient import TestClient
from presentation.api.app import app


def test_notion_oauth_start_and_callback_mock():
    client = TestClient(app)
    r = client.get("/oauth/start", params={"provider": "notion", "tenant_id": "tX"})
    assert r.status_code == 200
    data = r.json()
    assert "state" in data and "authorize_url" in data
    payload = {"provider": "notion", "code": "abc123", "state": data["state"]}
    r2 = client.post("/oauth/callback", json=payload)
    assert r2.status_code == 200
    j = r2.json()
    assert j.get("ok") is True
    assert j.get("tenant_id") == "tX"
    assert j.get("provider") == "notion"


def test_oauth_state_mismatch_rejected():
    client = TestClient(app)
    r = client.post("/oauth/callback", json={"provider": "nylas", "code": "x", "state": "bogus"})
    assert r.status_code == 401



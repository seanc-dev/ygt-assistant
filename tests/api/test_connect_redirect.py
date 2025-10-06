from fastapi.testclient import TestClient
from presentation.api.app import app

def test_connect_redirects_to_provider():
    client = TestClient(app)
    r = client.get("/connect", params={"provider":"notion","tenant_id":"t1"}, follow_redirects=False)
    assert r.status_code in (302,307)
    loc = r.headers["location"]
    assert "api.notion.com" in loc and "state=" in loc

import json
from presentation.api.app import app
from fastapi.testclient import TestClient


def test_actions_scan_returns_approvals():
    client = TestClient(app)
    r = client.post("/actions/scan", json={"domains": ["email", "calendar"]})
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert data and data[0]["status"] == "proposed"

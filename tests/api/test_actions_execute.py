from fastapi.testclient import TestClient
from presentation.api.app import app


def test_actions_execute_endpoint_returns_plan():
    client = TestClient(app)
    payload = {
        "actions": [
            {"type": "create_task", "payload": {"title": "Follow up", "source_ids": {"email_message_id": "m-xyz"}}}
        ],
        "dry_run": True,
    }
    r = client.post("/actions/execute", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data.get("dry_run") is True
    assert data.get("request_id")
    results = data.get("results", [])
    assert results and results[0].get("action") == "create_task"



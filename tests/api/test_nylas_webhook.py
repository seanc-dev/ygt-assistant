from fastapi.testclient import TestClient
from presentation.api.app import app


def test_nylas_email_created_triage_plan():
    client = TestClient(app)
    payload = {
        "type": "email.created",
        "data": {
            "id": "msg_123",
            "from": [{"email": "updates@client.com"}],
            "subject": "Monthly update and invoice",
            "snippet": "Hi team, here is the update and invoice...",
        },
    }
    r = client.post("/webhooks/nylas", json=payload)
    assert r.status_code == 200
    triage = r.json().get("triage", {})
    actions = triage.get("actions", [])
    assert isinstance(actions, list)
    assert any(a.get("type") == "create_task" for a in actions)

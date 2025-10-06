import os

from fastapi.testclient import TestClient
from presentation.api.app import app


def test_audit_roundtrip():
    client = TestClient(app)
    r1 = client.post(
        "/actions/execute",
        json={
            "actions": [
                {
                    "type": "create_task",
                    "payload": {"title": "A", "source_ids": {"email_message_id": "m-77"}},
                }
            ],
            "dry_run": True,
        },
    )
    rid = r1.json().get("request_id")
    client.post(
        "/admin/login",
        json={"email": "admin@example.com", "secret": os.environ["ADMIN_SECRET"]},
    )
    r2 = client.get(f"/audit/{rid}")
    assert r2.status_code == 200
    body = r2.json()
    assert body.get("request_id") == rid
    assert body.get("results")



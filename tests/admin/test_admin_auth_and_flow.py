import os


TEST_ADMIN_SECRET = "test-admin-secret-1234567890"
TEST_ENCRYPTION_KEY = "D_Jhyl9DGCCyOLU_qTzw3CSLinmvglzsXDbNSsmw24w="

os.environ.setdefault("TESTING", "true")
os.environ.setdefault("ADMIN_EMAIL", "admin@example.com")
os.environ.setdefault("ADMIN_SECRET", TEST_ADMIN_SECRET)
os.environ.setdefault("ENCRYPTION_KEY", TEST_ENCRYPTION_KEY)

from fastapi.testclient import TestClient
from presentation.api.app import app


def _login(client: TestClient):
    r = client.post(
        "/admin/login",
        json={"email": "admin@example.com", "secret": TEST_ADMIN_SECRET},
    )
    assert r.status_code == 200


def test_admin_requires_auth():
    client = TestClient(app)
    r = client.get("/admin/me")
    assert r.status_code == 401


def test_admin_create_tenant_and_rules_and_triage(monkeypatch):
    monkeypatch.setenv("ADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("ADMIN_SECRET", TEST_ADMIN_SECRET)
    client = TestClient(app)
    _login(client)

    r = client.post("/admin/tenants", params={"name": "Acme Co"})
    assert r.status_code == 200
    tid = r.json()["id"]

    rules_yaml = (
        'timezone: "Pacific/Auckland"\n'
        "email_triage:\n"
        "  - match:\n"
        "      from: ['*@client.com']\n"
        "      subject_has: ['update','invoice']\n"
        "    action: create_task\n"
        "    fields:\n"
        "      status: 'Next'\n"
        "      db: 'Tasks'\n"
    )
    r2 = client.put(f"/admin/tenants/{tid}/rules", json={"yaml_text": rules_yaml})
    assert r2.status_code == 200

    payload = {
        "message_id": "m123",
        "sender": "bob@client.com",
        "subject": "Monthly update and invoice",
        "body_text": "See attached",
        "received_at": "2025-09-06T00:00:00Z",
    }
    r3 = client.post(f"/admin/tenants/{tid}/triage/dry-run", json=payload)
    assert r3.status_code == 200
    actions = r3.json()["triage"]["actions"]
    assert any(a["type"] == "create_task" for a in actions)



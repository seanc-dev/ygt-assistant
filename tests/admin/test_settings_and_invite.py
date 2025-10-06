from fastapi.testclient import TestClient
from infra.smtp.mailer_repo import PostmarkMailer
import os


TEST_ADMIN_SECRET = "test-admin-secret-1234567890"
TEST_ENCRYPTION_KEY = "D_Jhyl9DGCCyOLU_qTzw3CSLinmvglzsXDbNSsmw24w="

os.environ.setdefault("TESTING", "true")
os.environ.setdefault("ADMIN_EMAIL", "admin@example.com")
os.environ.setdefault("ADMIN_SECRET", TEST_ADMIN_SECRET)
os.environ.setdefault("ENCRYPTION_KEY", TEST_ENCRYPTION_KEY)

from presentation.api.app import app


def _login(client: TestClient):
    client.post(
        "/admin/login",
        json={"email": "admin@example.com", "secret": TEST_ADMIN_SECRET},
    )


def test_settings_roundtrip_and_invite(monkeypatch):
    monkeypatch.setenv("ADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("ADMIN_SECRET", TEST_ADMIN_SECRET)
    from infra.memory.mailer_repo import MemoryMailer
    monkeypatch.setattr("presentation.api.app.mailer", lambda: MemoryMailer())
    client = TestClient(app)
    _login(client)
    r = client.post("/admin/tenants", params={"name": "Acme"})
    tid = r.json()["id"]
    body = {
        "data": {
            "client_email": "ceo@acme.com",
            "notion_tasks_db_id": "db_tasks",
            "notion_crm_db_id": "db_crm",
            "notion_sessions_db_id": "db_sessions",
        }
    }
    r2 = client.put(f"/admin/tenants/{tid}/settings", json=body)
    assert r2.status_code == 200
    r3 = client.get(f"/admin/tenants/{tid}/settings")
    s = r3.json()["settings"]
    assert s["client_email"] == "ceo@acme.com"
    r4 = client.post(f"/admin/tenants/{tid}/invite", json={"to_email": "ceo@acme.com"})
    assert r4.status_code == 200
    links = r4.json()["links"]
    assert "notion" in links and "nylas" in links


def test_invite_failure_surfaces(monkeypatch):
    monkeypatch.setenv("ADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("ADMIN_SECRET", TEST_ADMIN_SECRET)
    client = TestClient(app)
    _login(client)
    tid = client.post("/admin/tenants", params={"name": "Acme"}).json()["id"]

    class BoomMailer:
        def send(self, *args, **kwargs):
            raise RuntimeError("mailer down")

    monkeypatch.setattr("presentation.api.app.mailer", lambda: BoomMailer())

    resp = client.post(
        f"/admin/tenants/{tid}/invite",
        json={"to_email": "ceo@acme.com"},
    )

    assert resp.status_code == 502
    assert resp.json()["detail"] == "invite_send_failed"


def test_invite_uses_postmark_when_token_present(monkeypatch):
    monkeypatch.setenv("ADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("ADMIN_SECRET", TEST_ADMIN_SECRET)
    monkeypatch.setenv("POSTMARK_SERVER_TOKEN", "pm-test-token")
    monkeypatch.setenv("POSTMARK_MESSAGE_STREAM", "transactional")

    calls: dict[str, object] = {}

    def _fake_send(self, *args, **kwargs):
        calls["args"] = args
        calls["kwargs"] = kwargs

    monkeypatch.setattr(PostmarkMailer, "send", _fake_send)

    client = TestClient(app)
    _login(client)
    tenant = client.post("/admin/tenants", params={"name": "Acme"}).json()

    resp = client.post(
        f"/admin/tenants/{tenant['id']}/invite",
        json={"to_email": "ceo@acme.com"},
    )

    assert resp.status_code == 200
    assert "args" in calls or "kwargs" in calls
    recipient = None
    if "kwargs" in calls:
        recipient = calls["kwargs"].get("to")
    if not recipient and "args" in calls and calls["args"]:
        recipient = calls["args"][0]
    assert recipient == "ceo@acme.com"
    if "kwargs" in calls and "message_stream" in calls["kwargs"]:
        assert calls["kwargs"]["message_stream"] == "transactional"

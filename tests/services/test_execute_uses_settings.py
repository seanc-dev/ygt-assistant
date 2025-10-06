import os


TEST_ADMIN_SECRET = "test-admin-secret-1234567890"
TEST_ENCRYPTION_KEY = "D_Jhyl9DGCCyOLU_qTzw3CSLinmvglzsXDbNSsmw24w="

os.environ.setdefault("TESTING", "true")
os.environ.setdefault("ADMIN_EMAIL", "admin@example.com")
os.environ.setdefault("ADMIN_SECRET", TEST_ADMIN_SECRET)
os.environ.setdefault("ENCRYPTION_KEY", TEST_ENCRYPTION_KEY)

from fastapi.testclient import TestClient
from presentation.api.app import app

def test_execute_uses_tenant_notions_db_ids(monkeypatch):
    client = TestClient(app)
    client.post(
        "/admin/login",
        json={"email": "admin@example.com", "secret": TEST_ADMIN_SECRET},
    )
    r = client.post("/admin/tenants", params={"name":"Acme"})
    tid = r.json()["id"]
    client.put(f"/admin/tenants/{tid}/settings", json={"data":{"notion_tasks_db_id":"db_tasks_X","notion_crm_db_id":"db_crm_X","notion_sessions_db_id":"db_sessions_X"}})
    payload = {"actions":[{"type":"create_task","payload":{"title":"Follow up","source_ids":{"email_message_id":"m1"}}}],"dry_run": True, "tenant_id": tid}
    r2 = client.post("/actions/execute", json=payload)
    assert r2.status_code == 200
    res = r2.json()["results"][0]["result"]
    assert res["payload"]["parent"]["database_id"] == "db_tasks_X"

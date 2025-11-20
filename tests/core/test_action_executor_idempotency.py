from core.services.action_executor import execute_actions
from infra.repos.factory import idempotency_repo


def test_duplicate_execution_is_skipped(tmp_path, monkeypatch):
    db_path = tmp_path / "state.db"
    # force repo to use temp db
    idempotency_repo.cache_clear()  # type: ignore
    monkeypatch.setenv("DATA_STORE_PATH", str(db_path))

    actions = [
        {"type": "create_task", "payload": {"id": "t1", "external_id": "m1"}},
        {"type": "create_task", "payload": {"id": "t1", "external_id": "m1"}},
    ]
    first = execute_actions(actions, tenant_id="tenant-1")
    second = execute_actions(actions, tenant_id="tenant-1")

    skipped = [r for r in second["results"] if r.get("status") == "skipped_duplicate"]
    assert skipped, "duplicate actions should be skipped"


def test_audit_record_written(tmp_path, monkeypatch):
    db_path = tmp_path / "audit.db"
    from infra.repos.factory import audit_repo

    audit_repo.cache_clear()  # type: ignore
    idempotency_repo.cache_clear()  # type: ignore
    monkeypatch.setenv("DATA_STORE_PATH", str(db_path))

    out = execute_actions([
        {"type": "create_task", "payload": {"id": "t99", "external_id": "m99"}}
    ])
    rid = out["request_id"]
    record = audit_repo().get(rid)
    assert record is not None
    assert record["results"]

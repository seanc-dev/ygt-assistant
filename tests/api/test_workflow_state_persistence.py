from presentation.api.state import approvals_store, history_log
from infra.repos.factory import workflow_state_repo


def test_approvals_persist_across_instances(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_STORE_PATH", str(tmp_path / "state.db"))
    workflow_state_repo.cache_clear()  # type: ignore

    approvals_store["a1"] = {"id": "a1", "title": "Approve", "status": "proposed"}

    # create a new repo instance to simulate reload
    workflow_state_repo.cache_clear()  # type: ignore
    persisted = list(approvals_store.values())
    assert persisted and persisted[0]["id"] == "a1"


def test_history_records_ordered(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_STORE_PATH", str(tmp_path / "history.db"))
    workflow_state_repo.cache_clear()  # type: ignore

    history_log.append({"verb": "approve", "object": "approval", "id": "a1"})
    history_log.append({"verb": "edit", "object": "approval", "id": "a1"})

    entries = history_log.list(5)
    assert entries[0]["verb"] == "edit"
    assert entries[1]["verb"] == "approve"

from core.services.action_executor import execute_actions


def test_execute_actions_dry_run_and_idempotency():
    actions = [
        {"type": "create_task", "payload": {"title": "Update invoice", "source_ids": {"email_message_id": "m-1"}}},
        {"type": "create_task", "payload": {"title": "Update invoice", "source_ids": {"email_message_id": "m-1"}}},
        {"type": "upsert_contact", "payload": {"name": "Bob", "email": "bob@client.com", "source_ids": {"email_message_id": "m-2"}}},
    ]
    first = execute_actions(actions, dry_run=True, tenant_id="t1")
    assert first["dry_run"] is True
    statuses = [r.get("result", {}).get("dry_run") or r.get("status") for r in first["results"]]
    assert True in statuses  # at least one dry_run result present
    # run again to test duplicate skip
    second = execute_actions(actions, dry_run=True, tenant_id="t1")
    dup_statuses = [r.get("status") for r in second["results"] if r.get("status")]
    assert "skipped_duplicate" in dup_statuses



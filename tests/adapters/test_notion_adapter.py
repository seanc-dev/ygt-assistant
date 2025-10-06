from adapters.notion_adapter import NotionTasksAdapter, NotionCRMAdapter


def test_tasks_dry_run_payload_shape():
    a = NotionTasksAdapter()
    res = a.create_task(
        {"title": "Follow up", "due": {"date": "2025-09-07"}, "contact_notion_id": "abc"},
        dry_run=True,
    )
    assert res.get("dry_run") is True
    p = res.get("payload", {})
    assert p.get("parent", {}).get("database_id")
    assert "properties" in p and "Name" in p["properties"]


def test_crm_dry_run_payload_shape():
    a = NotionCRMAdapter()
    res = a.upsert_contact({"name": "Anna", "email": "anna@example.com"}, dry_run=True)
    assert res.get("dry_run") is True
    p = res.get("payload", {})
    assert p.get("parent", {}).get("database_id")
    assert p["properties"]["Name"]["title"]



from adapters.notion_adapter import NotionCRMAdapter


def test_upsert_contact_dry_run_includes_search_plan():
    a = NotionCRMAdapter()
    res = a.upsert_contact({"name": "Eve", "email": "eve@client.com"}, dry_run=True)
    plan = res.get("plan", {})
    assert plan.get("search")
    assert plan.get("create_if_absent")



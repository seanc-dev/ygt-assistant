from core.writer import write_semantic, write_narrative
from core.retrieval import recall_by_key, context_for


def test_write_and_recall_by_key():
    item = write_semantic("prefers_mornings", source="user")
    got = recall_by_key("prefers_mornings")
    assert any(i.id == item.id for i in got)


def test_context_for_groups_levels():
    write_narrative("Great week of progress", tags=["weekly"])  # ensure at least one narrative
    ctx = context_for("email")
    assert "narrative" in ctx

from core.chat.context import ThreadContext
from core.chat.focus import UiContext, resolve_focus_candidates
from core.chat.tokens import parse_message_with_tokens


def test_workroom_focus_defaults_to_current_task():
    ctx = ThreadContext(last_task_id="thread-task", last_project_id="proj-1")
    ui = UiContext(mode="workroom-task", workroom_task_id="active-task", workroom_project_id="proj-2")
    parsed = parse_message_with_tokens("Please help")

    candidates = resolve_focus_candidates(ctx, ui, parsed)
    assert candidates.default_task_id == "active-task"
    assert candidates.default_project_id == "proj-2"


def test_hub_focus_uses_suggested_task():
    ctx = ThreadContext()
    ui = UiContext(mode="hub", hub_suggested_task_id="suggested-task")
    parsed = parse_message_with_tokens("Need assistance")

    candidates = resolve_focus_candidates(ctx, ui, parsed)
    assert candidates.default_task_id == "suggested-task"

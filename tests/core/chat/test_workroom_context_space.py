from core.chat.workroom_context_space import build_workroom_context_space


def test_build_workroom_context_space_truncates_lists():
    context = {
        "projects": [
            {"id": f"proj-{i}", "name": f"Project {i}", "status": "active"}
            for i in range(5)
        ],
        "tasks": [
            {
                "id": f"task-{i}",
                "title": f"Task {i}",
                "status": "backlog",
                "project_id": "proj-1",
            }
            for i in range(15)
        ],
        "actions": [
            {"id": f"action-{i}", "preview": f"Action {i}", "source_type": "manual"}
            for i in range(12)
        ],
    }

    space = build_workroom_context_space(context, max_projects=3, max_tasks=10, max_actions=5)

    assert space
    context_input = space.to_context_input()
    assert len(context_input["projects"]) == 3
    assert len(context_input["tasks"]) == 10
    assert len(context_input["actions"]) == 5
    assert context_input["truncated"] == {"projects": 2, "tasks": 5, "actions": 7}


def test_build_workroom_context_space_omits_when_empty():
    space = build_workroom_context_space({}, focus_task_id=None, focus_project_id=None)
    assert space is None


def test_build_workroom_context_space_derives_anchor_project():
    context = {
        "tasks": [
            {
                "id": "task-1",
                "title": "Title",
                "status": "backlog",
                "project_id": "proj-99",
            }
        ],
        "projects": [
            {"id": "proj-99", "name": "Anchor Project", "status": "active"}
        ],
    }

    space = build_workroom_context_space(context, focus_task_id="task-1")
    context_input = space.to_context_input()

    assert context_input["anchor"] == {"task_id": "task-1", "project_id": "proj-99"}

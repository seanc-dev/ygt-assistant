"""API tests for create_task approvals via assistant endpoints."""

import uuid

import pytest
from fastapi.testclient import TestClient

from presentation.api.app import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _seed_workroom(client: TestClient) -> None:
    resp = client.post("/dev/workroom/seed")
    assert resp.status_code == 200


def _get_first_task_id(client: TestClient) -> str:
    resp = client.get("/api/workroom/tree")
    assert resp.status_code == 200
    tree = resp.json()["tree"]
    return tree[0]["children"][0]["id"]


def test_assistant_approve_create_task_success(client: TestClient) -> None:
    """Approving a unique create_task operation should succeed."""
    _seed_workroom(client)
    task_id = _get_first_task_id(client)

    operation = {
        "op": "create_task",
        "params": {
            "title": f"Plan Q1 roadmap {uuid.uuid4().hex[:6]}",
            "priority": "high",
            "project": "current project",
        },
    }

    resp = client.post(
        f"/api/workroom/tasks/{task_id}/assistant-approve",
        json={"operation": operation},
        cookies={"user_id": "test-user"},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["result"]["ok"] is True
    assert data["result"]["op"] == "create_task"


def test_assistant_approve_create_task_duplicate_returns_conflict(
    client: TestClient,
) -> None:
    """Approving the same create_task twice should raise a 409 with stock message."""
    _seed_workroom(client)
    task_id = _get_first_task_id(client)
    title = f"Plan Q1 roadmap {uuid.uuid4().hex[:6]}"

    operation = {
        "op": "create_task",
        "params": {
            "title": title,
            "priority": "high",
            "project": "current project",
        },
    }

    # First approval succeeds
    first = client.post(
        f"/api/workroom/tasks/{task_id}/assistant-approve",
        json={"operation": operation},
        cookies={"user_id": "test-user"},
    )
    assert first.status_code == 200

    # Second approval with same payload should conflict
    second = client.post(
        f"/api/workroom/tasks/{task_id}/assistant-approve",
        json={"operation": operation},
        cookies={"user_id": "test-user"},
    )

    assert second.status_code == 409
    detail = second.json()["detail"]
    assert (
        "assistant_message" in detail
        and "already has a task with that name" in detail["assistant_message"]
    )


def test_assistant_approve_rejects_invalid_priority(client: TestClient) -> None:
    """Server should reject invalid priority enums before execution."""
    _seed_workroom(client)
    task_id = _get_first_task_id(client)

    operation = {
        "op": "create_task",
        "params": {
            "title": "Plan roadmap",
            "priority": "highest",
        },
    }

    resp = client.post(
        f"/api/workroom/tasks/{task_id}/assistant-approve",
        json={"operation": operation},
        cookies={"user_id": "test-user"},
    )

    assert resp.status_code == 400
    assert "priority" in resp.json()["detail"]


def test_create_task_same_title_different_project_allowed(client: TestClient) -> None:
    """Duplicate titles in other projects should not block approval."""
    _seed_workroom(client)
    tree_resp = client.get("/api/workroom/tree")
    assert tree_resp.status_code == 200
    tree = tree_resp.json()["tree"]
    focus_project_id = tree[0]["id"]
    focus_task_id = tree[0]["children"][0]["id"]

    # Create another project
    other_project_resp = client.post(
        "/api/workroom/projects",
        json={"title": "Analytics"},
        cookies={"user_id": "test-user"},
    )
    assert other_project_resp.status_code == 200
    other_project_id = other_project_resp.json()["project"]["id"]

    # Create task with duplicate title in other project
    duplicate_title = "Cross-project duplicate task"
    create_task_resp = client.post(
        "/api/workroom/tasks",
        json={"projectId": other_project_id, "title": duplicate_title},
        cookies={"user_id": "test-user"},
    )
    assert create_task_resp.status_code == 200

    # Approve create_task in focus project with same title should succeed
    operation = {
        "op": "create_task",
        "params": {
            "title": duplicate_title,
            "priority": "medium",
            "project": "current project",
        },
    }

    resp = client.post(
        f"/api/workroom/tasks/{focus_task_id}/assistant-approve",
        json={"operation": operation},
        cookies={"user_id": "test-user"},
    )
    assert resp.status_code == 200
    assert resp.json()["result"]["ok"] is True

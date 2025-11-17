"""Tests for API endpoints returning stock messages for duplicate errors."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
from presentation.api.repos.workroom import DuplicateProjectNameError, DuplicateTaskTitleError


@pytest.fixture
def client():
    """Create test client."""
    from presentation.api.app import app
    return TestClient(app)


@patch("core.services.llm_executor.execute_single_op_approved")
@patch("core.services.llm_context_builder.build_context_for_user")
@patch("presentation.api.routes.workroom.workroom_repo")
@patch("presentation.api.repos.workroom._resolve_identity")
def test_assistant_approve_returns_409_for_duplicate_project(
    mock_resolve,
    mock_workroom,
    mock_context,
    mock_execute,
    client,
):
    """Test that duplicate project error returns 409 with stock message."""
    mock_resolve.return_value = ("tenant-1", "user-1")
    mock_workroom.get_task.return_value = {"id": "task-1", "thread_id": None}
    mock_context.return_value = {"projects": [], "tasks": []}
    mock_execute.return_value = {
        "ok": False,
        "op": "create_task",
        "params": {"title": "Test", "project": "Existing Project"},
        "error": "Project 'Existing Project' already exists.",
        "stock_message": "That project already exists. Would you like to name it something else?",
    }

    response = client.post(
        "/api/workroom/tasks/task-1/assistant-approve",
        json={
            "operation": {
                "op": "create_task",
                "params": {"title": "Test", "project": "Existing Project"},
            }
        },
        cookies={"user_id": "test-user"},
    )

    assert response.status_code == 409
    data = response.json()
    assert "detail" in data
    assert "stock_message" in data["detail"]
    assert "That project already exists" in data["detail"]["stock_message"]


@patch("core.services.llm_executor.execute_single_op_approved")
@patch("core.services.llm_context_builder.build_context_for_user")
@patch("presentation.api.routes.workroom.workroom_repo")
@patch("presentation.api.repos.workroom._resolve_identity")
def test_assistant_approve_returns_409_for_duplicate_task(
    mock_resolve,
    mock_workroom,
    mock_context,
    mock_execute,
    client,
):
    """Test that duplicate task error returns 409 with stock message."""
    mock_resolve.return_value = ("tenant-1", "user-1")
    mock_workroom.get_task.return_value = {"id": "task-1", "thread_id": None}
    mock_context.return_value = {"projects": [], "tasks": []}
    mock_execute.return_value = {
        "ok": False,
        "op": "create_task",
        "params": {"title": "Duplicate Task", "project": "My Project"},
        "error": "This project already has a task with that name.",
        "stock_message": "This project already has a task with that name. Would you like to name it something else?",
    }

    response = client.post(
        "/api/workroom/tasks/task-1/assistant-approve",
        json={
            "operation": {
                "op": "create_task",
                "params": {"title": "Duplicate Task", "project": "My Project"},
            }
        },
        cookies={"user_id": "test-user"},
    )

    assert response.status_code == 409
    data = response.json()
    assert "detail" in data
    assert "stock_message" in data["detail"]
    assert "already has a task with that name" in data["detail"]["stock_message"]


@patch("core.services.llm_executor.execute_single_op_approved")
@patch("core.services.llm_context_builder.build_context_for_user")
@patch("presentation.api.repos.tasks")
@patch("presentation.api.repos.workroom._resolve_identity")
def test_queue_assistant_approve_returns_409_for_duplicate(
    mock_resolve,
    mock_tasks,
    mock_context,
    mock_execute,
    client,
):
    """Test that queue assistant-approve returns 409 for duplicate errors."""
    mock_resolve.return_value = ("tenant-1", "user-1")
    mock_tasks.get_action_item.return_value = {"id": "action-1", "thread_id": None}
    mock_context.return_value = {"projects": [], "tasks": [], "actions": []}
    mock_execute.return_value = {
        "ok": False,
        "op": "create_task",
        "params": {"title": "Duplicate Task"},
        "error": "This project already has a task with that name.",
        "stock_message": "This project already has a task with that name. Would you like to name it something else?",
    }

    response = client.post(
        "/api/queue/action-1/assistant-approve",
        json={
            "operation": {
                "op": "create_task",
                "params": {"title": "Duplicate Task"},
            }
        },
        cookies={"user_id": "test-user"},
    )

    assert response.status_code == 409
    data = response.json()
    assert "detail" in data
    assert "stock_message" in data["detail"]


@patch("core.services.llm_executor.execute_single_op_approved")
@patch("core.services.llm_context_builder.build_context_for_user")
@patch("presentation.api.routes.workroom.workroom_repo")
@patch("presentation.api.repos.workroom._resolve_identity")
def test_assistant_approve_success_returns_200(
    mock_resolve,
    mock_workroom,
    mock_context,
    mock_execute,
    client,
):
    """Test that successful approval returns 200."""
    mock_resolve.return_value = ("tenant-1", "user-1")
    mock_workroom.get_task.return_value = {"id": "task-1", "thread_id": None}
    mock_context.return_value = {"projects": [], "tasks": []}
    mock_execute.return_value = {
        "ok": True,
        "op": "create_task",
        "params": {"title": "New Task"},
    }

    response = client.post(
        "/api/workroom/tasks/task-1/assistant-approve",
        json={
            "operation": {
                "op": "create_task",
                "params": {"title": "New Task"},
            }
        },
        cookies={"user_id": "test-user"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True


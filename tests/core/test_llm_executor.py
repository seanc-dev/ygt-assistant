"""Tests for LLM operations executor."""

import pytest
from unittest.mock import Mock, patch
from core.services.llm_executor import (
    execute_ops,
    execute_single_op_approved,
    _should_apply_operation,
    _get_risk_category,
    _execute_single_op,
)
from core.domain.llm_ops import ChatOp, CreateTaskOp, UpdateTaskStatusOp
from presentation.api.repos.workroom import DuplicateProjectNameError, DuplicateTaskTitleError


def test_get_risk_category():
    """Test risk category classification."""
    assert _get_risk_category(ChatOp(op="chat", params={"message": "Hi"})) == "low"
    assert (
        _get_risk_category(CreateTaskOp(op="create_task", params={"title": "Test"}))
        == "medium"
    )
    assert (
        _get_risk_category(
            UpdateTaskStatusOp(
                op="update_task_status", params={"task_id": "1", "status": "done"}
            )
        )
        == "medium"
    )


def test_should_apply_operation_training_wheels():
    """Test trust gating for training_wheels mode."""
    chat_op = ChatOp(op="chat", params={"message": "Hi"})
    task_op = CreateTaskOp(op="create_task", params={"title": "Test"})

    assert _should_apply_operation(chat_op, "training_wheels") is True
    assert _should_apply_operation(task_op, "training_wheels") is False


def test_should_apply_operation_supervised():
    """Test trust gating for supervised mode."""
    chat_op = ChatOp(op="chat", params={"message": "Hi"})
    task_op = CreateTaskOp(op="create_task", params={"title": "Test"})

    assert _should_apply_operation(chat_op, "supervised") is True
    assert _should_apply_operation(task_op, "supervised") is True


def test_should_apply_operation_autonomous():
    """Test trust gating for autonomous mode."""
    task_op = CreateTaskOp(op="create_task", params={"title": "Test"})
    assert _should_apply_operation(task_op, "autonomous") is True


@patch("presentation.api.repos.workroom")
@patch("presentation.api.repos.tasks")
def test_execute_ops_splits_applied_and_pending(mock_tasks, mock_workroom):
    """Test execute_ops splits operations correctly."""
    ops = [
        ChatOp(op="chat", params={"message": "Hi"}),
        CreateTaskOp(op="create_task", params={"title": "Test"}),
    ]

    mock_workroom.create_task.return_value = {"id": "task-1"}

    result = execute_ops(
        ops, tenant_id="tenant-1", user_id="user-1", trust_mode="training_wheels"
    )

    # Chat op always applied, task op pending in training_wheels
    assert len(result["applied"]) == 1
    assert len(result["pending"]) == 1
    assert result["applied"][0]["op"] == "chat"
    assert result["pending"][0]["op"] == "create_task"

    # Verify create_task was not called (it's pending)
    mock_workroom.create_task.assert_not_called()


@patch("presentation.api.repos.workroom")
@patch("presentation.api.repos.tasks")
def test_execute_ops_handles_errors(mock_tasks, mock_workroom):
    """Test execute_ops handles execution errors gracefully."""
    ops = [
        CreateTaskOp(op="create_task", params={"title": ""}),  # Invalid - missing title
    ]

    # Mock the validation error that occurs in _execute_single_op
    def mock_execute(op, *, tenant_id, user_id):
        if isinstance(op, CreateTaskOp) and not op.params.get("title"):
            raise ValueError("CreateTaskOp requires 'title' in params")

    with patch(
        "core.services.llm_executor._execute_single_op", side_effect=mock_execute
    ):
        result = execute_ops(
            ops, tenant_id="tenant-1", user_id="user-1", trust_mode="supervised"
        )

        assert len(result["errors"]) == 1
        assert "error" in result["errors"][0]


@patch("presentation.api.repos.workroom")
@patch("presentation.api.repos.tasks")
def test_execute_single_op_resolves_project_name(mock_tasks, mock_workroom):
    """Ensure CreateTaskOp resolves project names to IDs before creation."""
    op = CreateTaskOp(
        op="create_task",
        params={
            "title": "Review metrics",
            "project": "UI QA Project",  # Semantic reference
            "description": "",
            "priority": "high",
        },
    )

    context = {
        "projects": [
            {"id": "project-uuid", "name": "UI QA Project"},
            {"id": "other-project", "name": "Other"},
        ]
    }

    _execute_single_op(
        op,
        tenant_id="tenant-1",
        user_id="user-1",
        context=context,
    )

    mock_workroom.create_task.assert_called_once_with(
        user_id="user-1",
        title="Review metrics",
        project_id="project-uuid",
        importance="high",
        description=None,
        from_action_id=None,
    )


@patch("presentation.api.repos.workroom")
@patch("presentation.api.repos.tasks")
def test_execute_single_op_resolves_current_project(mock_tasks, mock_workroom):
    """Test that 'current project' resolves to focus task's project."""
    op = CreateTaskOp(
        op="create_task",
        params={
            "title": "New task",
            "project": "current project",
        },
    )

    context = {
        "projects": [{"id": "proj-1", "name": "My Project"}],
        "tasks": [{"id": "task-1", "project_id": "proj-1"}],
    }

    # Mock get_task to return the project_id
    mock_workroom.get_task.return_value = {"id": "task-1", "project_id": "proj-1"}

    _execute_single_op(
        op,
        tenant_id="tenant-1",
        user_id="user-1",
        context=context,
        focus_task_id="task-1",
    )

    mock_workroom.create_task.assert_called_once_with(
        user_id="user-1",
        title="New task",
        project_id="proj-1",
        importance="medium",
        description=None,
        from_action_id=None,
    )


@patch("presentation.api.repos.workroom")
def test_execute_single_op_resolves_this_task(mock_workroom):
    """Test that 'this task' resolves to focus task ID."""
    from core.domain.llm_ops import UpdateTaskStatusOp

    op = UpdateTaskStatusOp(
        op="update_task_status",
        params={
            "task": "this task",
            "status": "done",
        },
    )

    context = {
        "tasks": [{"id": "task-123", "title": "Do something"}],
    }

    _execute_single_op(
        op,
        tenant_id="tenant-1",
        user_id="user-1",
        context=context,
        focus_task_id="task-123",
    )

    mock_workroom.update_task_status.assert_called_once_with(
        "user-1",
        "task-123",
        "done",
    )


@patch("presentation.api.repos.workroom")
@patch("presentation.api.repos.tasks")
def test_execute_single_op_handles_duplicate_error(mock_tasks, mock_workroom):
    """Test that duplicate errors are raised correctly."""
    from presentation.api.repos.workroom import DuplicateTaskTitleError

    op = CreateTaskOp(
        op="create_task",
        params={
            "title": "Duplicate Task",
            "project": "My Project",
        },
    )

    context = {
        "projects": [{"id": "proj-1", "name": "My Project"}],
    }

    mock_workroom.get_projects.return_value = [
        {"id": "proj-1", "name": "My Project"}
    ]
    mock_workroom.get_tasks.return_value = [
        {"id": "task-1", "title": "Duplicate Task", "project_id": "proj-1"}
    ]
    mock_workroom.create_task.side_effect = DuplicateTaskTitleError(
        "This project already has a task with that name."
    )

    with pytest.raises(DuplicateTaskTitleError):
        _execute_single_op(
            op,
            tenant_id="tenant-1",
            user_id="user-1",
            context=context,
        )


@patch("presentation.api.repos.workroom")
def test_execute_single_op_approved_returns_stock_message_for_duplicate_project(mock_workroom):
    """Test that execute_single_op_approved returns stock message for duplicate project."""
    op = CreateTaskOp(
        op="create_task",
        params={
            "title": "New Task",
            "project": "Existing Project",
        },
    )

    context = {
        "projects": [{"id": "proj-1", "name": "Existing Project"}],
    }

    mock_workroom.get_projects.return_value = [
        {"id": "proj-1", "name": "Existing Project"}
    ]
    mock_workroom.create_task.side_effect = DuplicateProjectNameError(
        "Project 'Existing Project' already exists."
    )

    result = execute_single_op_approved(
        op,
        tenant_id="tenant-1",
        user_id="user-1",
        context=context,
    )

    assert result["ok"] is False
    assert "assistant_message" in result
    assert "That project already exists" in result["assistant_message"]


@patch("presentation.api.repos.workroom")
def test_execute_single_op_approved_returns_stock_message_for_duplicate_task(mock_workroom):
    """Test that execute_single_op_approved returns stock message for duplicate task."""
    op = CreateTaskOp(
        op="create_task",
        params={
            "title": "Duplicate Task",
            "project": "My Project",
        },
    )

    context = {
        "projects": [{"id": "proj-1", "name": "My Project"}],
    }

    mock_workroom.get_projects.return_value = [
        {"id": "proj-1", "name": "My Project"}
    ]
    mock_workroom.get_tasks.return_value = [
        {"id": "task-1", "title": "Duplicate Task", "project_id": "proj-1"}
    ]
    mock_workroom.create_task.side_effect = DuplicateTaskTitleError(
        "This project already has a task with that name."
    )

    result = execute_single_op_approved(
        op,
        tenant_id="tenant-1",
        user_id="user-1",
        context=context,
    )

    assert result["ok"] is False
    assert "assistant_message" in result
    assert "already has a task with that name" in result["assistant_message"]


@patch("presentation.api.repos.workroom")
def test_execute_single_op_approved_success_returns_ok(mock_workroom):
    """Test that successful execution returns ok=True."""
    op = CreateTaskOp(
        op="create_task",
        params={
            "title": "New Task",
            "project": "My Project",
        },
    )

    context = {
        "projects": [{"id": "proj-1", "name": "My Project"}],
    }

    mock_workroom.get_projects.return_value = [
        {"id": "proj-1", "name": "My Project"}
    ]
    mock_workroom.create_task.return_value = {"id": "task-1", "title": "New Task"}

    result = execute_single_op_approved(
        op,
        tenant_id="tenant-1",
        user_id="user-1",
        context=context,
    )

    assert result["ok"] is True
    assert "assistant_message" not in result

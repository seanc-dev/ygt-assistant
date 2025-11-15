"""Tests for LLM operations executor."""

import pytest
from unittest.mock import Mock, patch
from core.services.llm_executor import (
    execute_ops,
    _should_apply_operation,
    _get_risk_category,
)
from core.domain.llm_ops import ChatOp, CreateTaskOp, UpdateTaskStatusOp


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

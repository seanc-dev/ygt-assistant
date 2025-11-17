"""Tests for LLM operations domain models."""
import pytest
from core.domain.llm_ops import (
    validate_operation,
    parse_operations_response,
    ChatOp,
    CreateTaskOp,
    UpdateTaskStatusOp,
    LinkActionToTaskOp,
    UpdateActionStateOp,
)


def test_validate_chat_op():
    """Test ChatOp validation."""
    op = validate_operation({"op": "chat", "params": {"message": "Hello"}})
    assert isinstance(op, ChatOp)
    assert op.op == "chat"
    assert op.params["message"] == "Hello"


def test_validate_create_task_op():
    """Test CreateTaskOp validation."""
    op = validate_operation({
        "op": "create_task",
        "params": {"title": "Test task", "project_id": "proj-123"}
    })
    assert isinstance(op, CreateTaskOp)
    assert op.op == "create_task"
    assert op.params["title"] == "Test task"


def test_validate_update_task_status_op():
    """Test UpdateTaskStatusOp validation."""
    op = validate_operation({
        "op": "update_task_status",
        "params": {"task_id": "task-123", "status": "done"}
    })
    assert isinstance(op, UpdateTaskStatusOp)
    assert op.op == "update_task_status"
    assert op.params["status"] == "done"


def test_validate_link_action_to_task_op():
    """Test LinkActionToTaskOp validation."""
    op = validate_operation({
        "op": "link_action_to_task",
        "params": {"action_id": "action-123", "task_id": "task-456"}
    })
    assert isinstance(op, LinkActionToTaskOp)
    assert op.op == "link_action_to_task"


def test_validate_update_action_state_op():
    """Test UpdateActionStateOp validation."""
    op = validate_operation({
        "op": "update_action_state",
        "params": {"action_id": "action-123", "state": "deferred", "defer_until": "2024-01-01T12:00:00Z"}
    })
    assert isinstance(op, UpdateActionStateOp)
    assert op.op == "update_action_state"


def test_validate_create_task_op_invalid_priority():
    """Invalid priority should raise ValueError."""
    with pytest.raises(ValueError, match="priority"):
        validate_operation(
            {
                "op": "create_task",
                "params": {"title": "Test task", "priority": "highest"},
            }
        )


def test_validate_update_task_status_invalid_status():
    """Invalid status should raise ValueError."""
    with pytest.raises(ValueError, match="status"):
        validate_operation(
            {
                "op": "update_task_status",
                "params": {"task_id": "task-123", "status": "nearly-done"},
            }
        )


def test_validate_update_action_state_invalid_state():
    """Invalid action state should raise ValueError."""
    with pytest.raises(ValueError, match="state"):
        validate_operation(
            {
                "op": "update_action_state",
                "params": {"action_id": "action-123", "state": "sending"},
            }
        )


def test_validate_missing_op_field():
    """Test validation fails when op field is missing."""
    with pytest.raises(ValueError, match="Operation missing 'op' field"):
        validate_operation({"params": {}})


def test_validate_missing_required_params():
    """Test validation fails when required params are missing."""
    with pytest.raises(ValueError, match="CreateTaskOp requires 'title' in params"):
        validate_operation({"op": "create_task", "params": {}})


def test_parse_operations_response():
    """Test parsing operations response."""
    response = {
        "operations": [
            {"op": "chat", "params": {"message": "Hello"}},
            {"op": "create_task", "params": {"title": "Test"}},
        ]
    }
    ops = parse_operations_response(response)
    assert len(ops) == 2
    assert isinstance(ops[0], ChatOp)
    assert isinstance(ops[1], CreateTaskOp)


def test_parse_operations_response_invalid_skipped():
    """Test that invalid operations are skipped during parsing."""
    response = {
        "operations": [
            {"op": "chat", "params": {"message": "Hello"}},
            {"op": "invalid_op", "params": {}},  # Invalid, should be skipped
            {"op": "create_task", "params": {"title": "Test"}},
        ]
    }
    ops = parse_operations_response(response)
    assert len(ops) == 2  # Invalid op skipped


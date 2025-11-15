"""LLM Operations Protocol - Domain Models.

Defines structured operations that the LLM can propose and execute.
All operations follow the pattern: { "op": "...", "params": { ... } }
"""

from __future__ import annotations

from typing import Literal, Optional, Union
from pydantic import BaseModel, Field


LlmOpType = Literal[
    "chat",
    "create_task",
    "update_task_status",
    "link_action_to_task",
    "update_action_state",
    "delete_project",
    "delete_task",
]


class ChatOp(BaseModel):
    """Chat operation - assistant message."""

    op: Literal["chat"] = "chat"
    params: dict[str, str] = Field(..., description="Must contain 'message' key")


class CreateTaskOp(BaseModel):
    """Create a new task."""

    op: Literal["create_task"] = "create_task"
    params: dict[str, Optional[str]] = Field(
        ...,
        description="Must contain 'title'; optional: 'project_id', 'description', 'priority', 'from_action_id'",
    )


class UpdateTaskStatusOp(BaseModel):
    """Update task status."""

    op: Literal["update_task_status"] = "update_task_status"
    params: dict[str, str] = Field(
        ..., description="Must contain 'task_id' and 'status'"
    )


class LinkActionToTaskOp(BaseModel):
    """Link an action item to a task."""

    op: Literal["link_action_to_task"] = "link_action_to_task"
    params: dict[str, str] = Field(
        ..., description="Must contain 'action_id' and 'task_id'"
    )


class UpdateActionStateOp(BaseModel):
    """Update action item state."""

    op: Literal["update_action_state"] = "update_action_state"
    params: dict[str, Optional[str | bool]] = Field(
        ...,
        description="Must contain 'action_id' and 'state'; optional: 'defer_until', 'added_to_today'",
    )


class DeleteProjectOp(BaseModel):
    """Delete one or more projects (soft delete)."""

    op: Literal["delete_project"] = "delete_project"
    params: dict[str, list[str]] = Field(
        ..., description="Must contain 'project_ids' list"
    )


class DeleteTaskOp(BaseModel):
    """Delete one or more tasks (soft delete)."""

    op: Literal["delete_task"] = "delete_task"
    params: dict[str, list[str]] = Field(
        ..., description="Must contain 'task_ids' list"
    )


# Discriminated union for all operations
LlmOperation = Union[
    ChatOp,
    CreateTaskOp,
    UpdateTaskStatusOp,
    LinkActionToTaskOp,
    UpdateActionStateOp,
    DeleteProjectOp,
    DeleteTaskOp,
]


def validate_operation(data: dict | LlmOperation) -> LlmOperation:
    """Validate and parse an operation dict into a typed LlmOperation.

    Raises ValueError if the operation is invalid.
    Accepts either a dict or an already-validated LlmOperation instance.
    """
    # If already a LlmOperation instance, return as-is
    if isinstance(data, LlmOperation):
        return data

    # Otherwise, treat as dict
    op_type = data.get("op")
    if not op_type:
        raise ValueError("Operation missing 'op' field")

    params = data.get("params", {})

    if op_type == "chat":
        if "message" not in params:
            raise ValueError("ChatOp requires 'message' in params")
        return ChatOp(op="chat", params=params)

    elif op_type == "create_task":
        if "title" not in params:
            raise ValueError("CreateTaskOp requires 'title' in params")
        return CreateTaskOp(op="create_task", params=params)

    elif op_type == "update_task_status":
        if "task_id" not in params or "status" not in params:
            raise ValueError(
                "UpdateTaskStatusOp requires 'task_id' and 'status' in params"
            )
        return UpdateTaskStatusOp(op="update_task_status", params=params)

    elif op_type == "link_action_to_task":
        if "action_id" not in params or "task_id" not in params:
            raise ValueError(
                "LinkActionToTaskOp requires 'action_id' and 'task_id' in params"
            )
        return LinkActionToTaskOp(op="link_action_to_task", params=params)

    elif op_type == "update_action_state":
        if "action_id" not in params or "state" not in params:
            raise ValueError(
                "UpdateActionStateOp requires 'action_id' and 'state' in params"
            )
        return UpdateActionStateOp(op="update_action_state", params=params)

    elif op_type == "delete_project":
        if "project_ids" not in params or not isinstance(params.get("project_ids"), list):
            raise ValueError(
                "DeleteProjectOp requires 'project_ids' list in params"
            )
        if not params["project_ids"]:
            raise ValueError("DeleteProjectOp requires at least one project_id")
        return DeleteProjectOp(op="delete_project", params=params)

    elif op_type == "delete_task":
        if "task_ids" not in params or not isinstance(params.get("task_ids"), list):
            raise ValueError(
                "DeleteTaskOp requires 'task_ids' list in params"
            )
        if not params["task_ids"]:
            raise ValueError("DeleteTaskOp requires at least one task_id")
        return DeleteTaskOp(op="delete_task", params=params)

    else:
        raise ValueError(f"Unknown operation type: {op_type}")


def parse_operations_response(data: dict) -> list[LlmOperation]:
    """Parse a response dict with 'operations' array into typed operations.

    Expected format: { "operations": [ { "op": "...", "params": {...} }, ... ] }
    """
    operations = data.get("operations", [])
    if not isinstance(operations, list):
        raise ValueError("Expected 'operations' to be a list")

    result = []
    for op_data in operations:
        try:
            op = validate_operation(op_data)
            result.append(op)
        except ValueError as e:
            # Log but continue parsing other operations
            import logging

            logging.getLogger(__name__).warning(
                f"Invalid operation skipped: {e}, data: {op_data}"
            )

    return result

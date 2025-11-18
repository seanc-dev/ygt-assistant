"""LLM Operations Executor with Trust Gating.

Executes LLM-proposed operations based on trust level and risk assessment.
Splits operations into "applied" (executed) and "pending" (requires approval).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Literal, Optional

from core.domain.llm_ops import (
    LlmOperation,
    ChatOp,
    CreateTaskOp,
    UpdateTaskStatusOp,
    LinkActionToTaskOp,
    UpdateActionStateOp,
    DeleteProjectOp,
    DeleteTaskOp,
    PriorityLiteral,
    TaskStatusLiteral,
    ActionStateLiteral,
)
from core.services.llm_context_builder import _get_current_project_id

logger = logging.getLogger(__name__)

TrustMode = Literal["training_wheels", "supervised", "autonomous"]

PRIORITY_VALUES = set(PriorityLiteral.__args__)
TASK_STATUS_VALUES = set(TaskStatusLiteral.__args__)
ACTION_STATE_VALUES = set(ActionStateLiteral.__args__)


class MultipleMatchesError(Exception):
    """Raised when a semantic reference matches multiple items."""

    pass


def _normalize_enum_value(
    value: Optional[str],
    *,
    allowed: set[str],
    field: str,
    op_type: str,
    default: Optional[str] = None,
) -> Optional[str]:
    """Normalize enum-like user input, logging if coercion is needed."""
    if value is None:
        return default

    normalized = str(value).strip().lower()
    if normalized in allowed:
        return normalized

    fallback = default if default is not None else None
    logger.warning(
        "Invalid %s '%s' for %s operation; using fallback '%s'",
        field,
        value,
        op_type,
        fallback,
    )
    return fallback


def _resolve_project_id(
    ref: Optional[str],
    context: Optional[Dict[str, Any]],
    focus_task_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> Optional[str]:
    """Resolve a project reference to a UUID.

    Args:
        ref: Project name, "current project", or UUID
        context: Context dict with projects list
        focus_task_id: Optional focus task ID to determine "current project"
        user_id: User ID for loading projects if context not provided

    Returns:
        Project UUID or None if not found/not specified

    Raises:
        MultipleMatchesError: If multiple projects match the name
    """
    if not ref:
        return _get_current_project_id(context or {}, focus_task_id, user_id)

    ref_str = str(ref).strip()

    # Check if it's already a UUID (36 chars with dashes)
    if len(ref_str) == 36 and ref_str.count("-") == 4:
        return ref_str

    # Handle "current project" alias
    if ref_str.lower() in ("current project", "this project", "current"):
        if focus_task_id and user_id:
            from presentation.api.repos import workroom

            try:
                task = workroom.get_task(user_id, focus_task_id)
                return task.get("project_id")
            except ValueError:
                pass
        return None

    # Resolve by name
    projects = []
    if context and "projects" in context:
        projects = context["projects"]
    elif user_id:
        from presentation.api.repos import workroom

        projects = workroom.get_projects(user_id)

    ref_lower = ref_str.lower()
    matches = [p for p in projects if p.get("name", "").lower().strip() == ref_lower]

    if len(matches) > 1:
        raise MultipleMatchesError(
            f"Multiple projects named '{ref_str}' found. Please specify which one."
        )
    elif len(matches) == 1:
        return matches[0]["id"]

    logger.warning(
        "Project reference '%s' not found. Available projects: %s",
        ref_str,
        [p.get("name") for p in projects],
    )
    raise ValueError(f"Project '{ref_str}' not found")


def _resolve_task_id(
    ref: Optional[str],
    context: Optional[Dict[str, Any]],
    focus_task_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> str:
    """Resolve a task reference to a UUID.

    Args:
        ref: Task title, "this task", or UUID
        context: Context dict with tasks list
        focus_task_id: Optional focus task ID for "this task" alias
        user_id: User ID for loading tasks if context not provided

    Returns:
        Task UUID

    Raises:
        ValueError: If task not found
        MultipleMatchesError: If multiple tasks match the title
    """
    if not ref:
        raise ValueError("Task reference is required")

    ref_str = str(ref).strip()

    # Check if it's already a UUID
    if len(ref_str) == 36 and ref_str.count("-") == 4:
        return ref_str

    # Handle "this task" alias
    if ref_str.lower() in ("this task", "current task", "the task"):
        if focus_task_id:
            return focus_task_id
        raise ValueError("'this task' reference requires a focus task")

    # Resolve by title
    tasks = []
    if context and "tasks" in context:
        tasks = context["tasks"]
    elif user_id:
        from presentation.api.repos import workroom

        tasks = workroom.get_tasks(user_id)

    ref_lower = ref_str.lower()
    matches = [t for t in tasks if t.get("title", "").lower().strip() == ref_lower]

    if len(matches) > 1:
        raise MultipleMatchesError(
            f"Multiple tasks named '{ref_str}' found. Please specify which one."
        )
    elif len(matches) == 1:
        return matches[0]["id"]

    raise ValueError(f"Task '{ref_str}' not found")


def _resolve_action_id(
    ref: Optional[str],
    context: Optional[Dict[str, Any]],
    focus_action_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> str:
    """Resolve an action reference to a UUID.

    Args:
        ref: Action preview/subject or UUID
        context: Context dict with actions list
        focus_action_id: Optional focus action ID
        user_id: User ID for loading actions if context not provided

    Returns:
        Action UUID

    Raises:
        ValueError: If action not found
        MultipleMatchesError: If multiple actions match
    """
    if not ref:
        raise ValueError("Action reference is required")

    ref_str = str(ref).strip()

    # Check if it's already a UUID
    if len(ref_str) == 36 and ref_str.count("-") == 4:
        return ref_str

    # Resolve by preview/subject
    actions = []
    if context and "actions" in context:
        actions = context["actions"]
    elif user_id:
        from presentation.api.repos import queue

        actions = queue.get_queue_items(user_id, limit=100)

    ref_lower = ref_str.lower()
    matches = []
    for action in actions:
        preview = (
            action.get("preview", "")
            or action.get("payload", {}).get("preview", "")
            or action.get("payload", {}).get("subject", "")
        )
        if preview.lower().strip() == ref_lower:
            matches.append(action)

    if len(matches) > 1:
        raise MultipleMatchesError(
            f"Multiple actions matching '{ref_str}' found. Please specify which one."
        )
    elif len(matches) == 1:
        return matches[0]["id"]

    raise ValueError(f"Action '{ref_str}' not found")


def _generate_error_chat_message(op: LlmOperation, error: str) -> str:
    """Generate a user-friendly chat message explaining why an operation failed.

    Args:
        op: The operation that failed
        error: The error message

    Returns:
        User-friendly error message, or None if no message should be generated
    """
    op_type = op.op

    # Don't generate error messages for chat operations (would be recursive)
    if op_type == "chat":
        return None

    # Generate context-aware error messages
    if op_type == "delete_project":
        project_ids = op.params.get("project_ids", [])
        if len(project_ids) == 1:
            return f"I couldn't delete the project: {error}. Please check the project name and try again."
        else:
            return f"I couldn't delete {len(project_ids)} projects: {error}. Please check the project names and try again."

    elif op_type == "delete_task":
        task_ids = op.params.get("task_ids", [])
        if len(task_ids) == 1:
            return f"I couldn't delete the task: {error}. Please check the task and try again."
        else:
            return f"I couldn't delete {len(task_ids)} tasks: {error}. Please check the tasks and try again."

    elif op_type == "create_task":
        return f"I couldn't create the task: {error}. Please check your request and try again."

    elif op_type == "update_task_status":
        return f"I couldn't update the task status: {error}. Please check the task ID and status value."

    elif op_type == "link_action_to_task":
        return f"I couldn't link the action to the task: {error}. Please check the action and task IDs."

    elif op_type == "update_action_state":
        return f"I couldn't update the action state: {error}. Please check the action ID and state value."

    else:
        return (
            f"I couldn't complete the requested operation: {error}. Please try again."
        )


def _get_risk_category(op: LlmOperation) -> str:
    """Classify operation risk level.

    Returns:
        "low", "medium", or "high"
    """
    if isinstance(op, ChatOp):
        return "low"
    elif isinstance(op, (DeleteProjectOp, DeleteTaskOp)):
        # Deletion operations are destructive and high risk
        return "high"
    elif isinstance(op, (CreateTaskOp, UpdateTaskStatusOp, LinkActionToTaskOp)):
        return "medium"
    elif isinstance(op, UpdateActionStateOp):
        # Check if this has external consequences (future: e.g., "send email")
        # For now, all action state updates are medium risk
        # Future: if state involves external actions, mark as high
        return "medium"
    else:
        return "medium"


def _should_apply_operation(op: LlmOperation, trust_mode: TrustMode) -> bool:
    """Determine if an operation should be auto-applied based on trust mode and risk.

    Rules:
    - training_wheels: Only low-risk ops auto-apply
    - supervised: Low and medium-risk ops auto-apply
    - autonomous: All ops auto-apply
    """
    risk = _get_risk_category(op)

    if trust_mode == "autonomous":
        return True
    elif trust_mode == "supervised":
        return risk in ["low", "medium"]
    elif trust_mode == "training_wheels":
        return risk == "low"
    return False


def execute_ops(
    ops: List[LlmOperation],
    *,
    tenant_id: str,
    user_id: str,
    trust_mode: TrustMode,
    thread_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Execute LLM operations with trust gating.

    Args:
        ops: List of operations to execute
        tenant_id: Tenant identifier
        user_id: User identifier
        trust_mode: Trust level for auto-application
        thread_id: Optional thread ID for ChatOp message creation
        context: Optional context dict with projects, tasks, actions, focus_item

    Returns:
        Dict with "applied", "pending", and "errors" lists
    """
    applied: List[Dict[str, Any]] = []
    pending: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []

    # Extract focus IDs from context
    focus_task_id = None
    focus_action_id = None
    if context and "focus_item" in context:
        focus_item = context["focus_item"]
        if focus_item.get("type") == "task":
            focus_task_id = focus_item.get("id")
        elif focus_item.get("type") == "action":
            focus_action_id = focus_item.get("id")

    for op in ops:
        op_dict = {"op": op.op, "params": op.params}

        # Check if operation should be auto-applied
        if _should_apply_operation(op, trust_mode):
            try:
                _execute_single_op(
                    op,
                    tenant_id=tenant_id,
                    user_id=user_id,
                    thread_id=thread_id,
                    context=context,
                    focus_task_id=focus_task_id,
                    focus_action_id=focus_action_id,
                )
                applied.append(op_dict)
            except Exception as e:
                logger.error(f"Failed to execute operation {op.op}: {e}", exc_info=True)
                errors.append(
                    {
                        "op": op.op,
                        "params": op.params,
                        "error": str(e),
                    }
                )
                # Graceful degradation: generate chat operation explaining the failure
                error_message = _generate_error_chat_message(op, str(e))
                if error_message:
                    # Add chat operation to response even without thread_id (for UI feedback)
                    chat_op_dict = {"op": "chat", "params": {"message": error_message}}

                    # Try to execute if thread_id is available
                    if thread_id:
                        try:
                            chat_op = ChatOp(
                                op="chat", params={"message": error_message}
                            )
                            _execute_single_op(
                                chat_op,
                                tenant_id=tenant_id,
                                user_id=user_id,
                                thread_id=thread_id,
                                context=context,
                                focus_task_id=focus_task_id,
                                focus_action_id=focus_action_id,
                            )
                            applied.append(chat_op_dict)
                        except Exception as chat_error:
                            logger.warning(
                                f"Failed to execute error chat message: {chat_error}"
                            )
                            # Still add to applied even if execution fails (for UI feedback)
                            applied.append(chat_op_dict)
                    else:
                        # No thread_id - still add chat operation for UI feedback
                        # but log that execution was skipped
                        logger.debug(
                            "Error chat message generated but no thread_id - adding to response for UI feedback"
                        )
                        applied.append(chat_op_dict)
        else:
            # Operation requires approval
            pending.append(op_dict)

    return {
        "applied": applied,
        "pending": pending,
        "errors": errors,
    }


def execute_single_op_approved(
    op: LlmOperation,
    *,
    tenant_id: str,
    user_id: str,
    thread_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Execute a single operation that was explicitly approved by the user.

    This bypasses trust gating since the user has explicitly approved the operation.

    Args:
        op: Operation to execute
        tenant_id: Tenant identifier
        user_id: User identifier
        thread_id: Optional thread ID for ChatOp message creation
        context: Optional context dict with projects, tasks, actions, focus_item

    Returns:
        Dict with operation result, including stock messages for duplicate errors
    """
    # Extract focus IDs from context
    focus_task_id = None
    focus_action_id = None
    if context and "focus_item" in context:
        focus_item = context["focus_item"]
        if focus_item.get("type") == "task":
            focus_task_id = focus_item.get("id")
        elif focus_item.get("type") == "action":
            focus_action_id = focus_item.get("id")

    try:
        _execute_single_op(
            op,
            tenant_id=tenant_id,
            user_id=user_id,
            thread_id=thread_id,
            context=context,
            focus_task_id=focus_task_id,
            focus_action_id=focus_action_id,
        )
        return {"ok": True, "op": op.op, "params": op.params}
    except Exception as e:
        # Generate chat feedback for the user if possible
        error_message = _generate_error_chat_message(op, str(e))
        if error_message and thread_id:
            try:
                chat_op = ChatOp(op="chat", params={"message": error_message})
                _execute_single_op(
                    chat_op,
                    tenant_id=tenant_id,
                    user_id=user_id,
                    thread_id=thread_id,
                    context=context,
                    focus_task_id=focus_task_id,
                    focus_action_id=focus_action_id,
                )
            except Exception as chat_error:
                logger.warning(
                    f"Failed to execute error chat message for approved operation {op.op}: {chat_error}"
                )

        # Handle duplicate errors with stock messages
        from presentation.api.repos.workroom import (
            DuplicateProjectNameError,
            DuplicateTaskTitleError,
        )

        if isinstance(e, DuplicateProjectNameError):
            assistant_message = (
                "That project already exists. Would you like to name it something else?"
            )
            return {
                "ok": False,
                "op": op.op,
                "params": op.params,
                "error": str(e),
                "assistant_message": assistant_message,
            }
        elif isinstance(e, DuplicateTaskTitleError):
            assistant_message = "This project already has a task with that name. Would you like to name it something else?"
            return {
                "ok": False,
                "op": op.op,
                "params": op.params,
                "error": str(e),
                "assistant_message": assistant_message,
            }

        logger.error(
            f"Failed to execute approved operation {op.op}: {e}", exc_info=True
        )
        return {"ok": False, "op": op.op, "params": op.params, "error": str(e)}


def undo_operation(
    op: LlmOperation,
    *,
    tenant_id: str,  # noqa: ARG001
    user_id: str,
    original_state: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Undo a previously applied operation.

    Args:
        op: Operation to undo
        tenant_id: Tenant identifier
        user_id: User identifier
        original_state: Optional original state before the operation (for restore)

    Returns:
        Dict with undo result
    """
    try:
        if isinstance(op, CreateTaskOp):
            # Undo: Delete the created task
            task_id = op.params.get("task_id") or (
                original_state and original_state.get("created_task_id")
            )
            if not task_id:
                raise ValueError("Cannot undo create_task: task_id not found")
            from presentation.api.repos import workroom

            # Mark task as archived (soft delete)
            # Note: "archived" is a valid status in the tasks table
            try:
                workroom.update_task_status(user_id, task_id, "archived")
            except Exception:
                # If archived doesn't work, try "backlog" as fallback
                # The task will still exist but won't show in normal views
                logger.warning(
                    f"Could not archive task {task_id}, marking as backlog instead"
                )
                workroom.update_task_status(user_id, task_id, "backlog")
            return {"ok": True, "op": "undo_create_task", "task_id": task_id}

        elif isinstance(op, UpdateTaskStatusOp):
            # Undo: Restore previous status
            task_id = op.params.get("task_id")
            previous_status = (
                original_state.get("previous_status") if original_state else "backlog"
            )
            if not task_id:
                raise ValueError("Cannot undo update_task_status: task_id not found")
            from presentation.api.repos import workroom

            workroom.update_task_status(user_id, task_id, previous_status)
            return {
                "ok": True,
                "op": "undo_update_task_status",
                "task_id": task_id,
                "restored_status": previous_status,
            }

        elif isinstance(op, LinkActionToTaskOp):
            # Undo: Unlink action from task
            action_id = op.params.get("action_id")
            task_id = op.params.get("task_id")
            if not action_id or not task_id:
                raise ValueError(
                    "Cannot undo link_action_to_task: action_id or task_id not found"
                )
            from presentation.api.repos import tasks

            # Unlink by setting task_id to None
            tasks.update_action_task_link(user_id, action_id, None)
            # Delete task_action_links entry
            try:
                links = tasks.get_task_action_links(user_id, task_id)
                for link in links:
                    if link.get("action_id") == action_id:
                        from presentation.api.repos.workroom import _resolve_identity

                        tenant_id_resolved, _ = _resolve_identity(user_id)
                        from archive.infra.supabase.client import client

                        with client() as c:
                            c.delete(
                                f"/task_action_links",
                                params={
                                    "tenant_id": f"eq.{tenant_id_resolved}",
                                    "id": f"eq.{link['id']}",
                                },
                            )
            except Exception as e:
                logger.warning(f"Failed to delete task_action_link: {e}")
            return {
                "ok": True,
                "op": "undo_link_action_to_task",
                "action_id": action_id,
                "task_id": task_id,
            }

        elif isinstance(op, UpdateActionStateOp):
            # Undo: Restore previous state
            action_id = op.params.get("action_id")
            previous_state = (
                original_state.get("previous_state") if original_state else "queued"
            )
            previous_defer_until = (
                original_state.get("previous_defer_until") if original_state else None
            )
            previous_added_to_today = (
                original_state.get("previous_added_to_today")
                if original_state
                else None
            )
            if not action_id:
                raise ValueError("Cannot undo update_action_state: action_id not found")
            from presentation.api.repos import tasks

            tasks.update_action_state(
                user_id,
                action_id,
                state=previous_state,
                defer_until=previous_defer_until,
                added_to_today=previous_added_to_today,
            )
            return {
                "ok": True,
                "op": "undo_update_action_state",
                "action_id": action_id,
                "restored_state": previous_state,
            }

        elif isinstance(op, DeleteProjectOp):
            # Undo: Restore deleted_at = NULL for project and cascaded tasks
            project_ids = op.params.get("project_ids", [])
            if not project_ids:
                raise ValueError("Cannot undo delete_project: project_ids not found")

            from presentation.api.repos import workroom
            from archive.infra.supabase.client import client

            tenant_id_resolved, _ = workroom._resolve_identity(user_id)
            restored_projects = []
            restored_tasks_count = 0

            for project_id in project_ids:
                # Restore project
                with client() as c:
                    resp = c.patch(
                        "/projects",
                        params={
                            "tenant_id": f"eq.{tenant_id_resolved}",
                            "id": f"eq.{project_id}",
                        },
                        json={"deleted_at": None},
                        headers={"Prefer": "return=representation"},
                    )
                    resp.raise_for_status()
                    restored_projects.append(project_id)

                # Restore cascaded tasks (if original_state has task info)
                if original_state:
                    task_ids = original_state.get("cascaded_task_ids", {}).get(
                        project_id, []
                    )
                    for task_id in task_ids:
                        try:
                            with client() as c:
                                resp = c.patch(
                                    "/tasks",
                                    params={
                                        "tenant_id": f"eq.{tenant_id_resolved}",
                                        "id": f"eq.{task_id}",
                                    },
                                    json={"deleted_at": None},
                                    headers={"Prefer": "return=representation"},
                                )
                                resp.raise_for_status()
                                restored_tasks_count += 1
                        except Exception as e:
                            logger.warning(f"Failed to restore task {task_id}: {e}")

            return {
                "ok": True,
                "op": "undo_delete_project",
                "project_ids": restored_projects,
                "tasks_restored": restored_tasks_count,
            }

        elif isinstance(op, DeleteTaskOp):
            # Undo: Restore deleted_at = NULL for tasks
            task_ids = op.params.get("task_ids", [])
            if not task_ids:
                raise ValueError("Cannot undo delete_task: task_ids not found")

            from presentation.api.repos import workroom
            from archive.infra.supabase.client import client

            tenant_id_resolved, _ = workroom._resolve_identity(user_id)
            restored_tasks = []

            for task_id in task_ids:
                try:
                    with client() as c:
                        resp = c.patch(
                            "/tasks",
                            params={
                                "tenant_id": f"eq.{tenant_id_resolved}",
                                "id": f"eq.{task_id}",
                            },
                            json={"deleted_at": None},
                            headers={"Prefer": "return=representation"},
                        )
                        resp.raise_for_status()
                        restored_tasks.append(task_id)
                except Exception as e:
                    logger.warning(f"Failed to restore task {task_id}: {e}")

            return {
                "ok": True,
                "op": "undo_delete_task",
                "task_ids": restored_tasks,
            }

        elif isinstance(op, ChatOp):
            # Chat ops can't be undone
            return {"ok": False, "error": "Cannot undo chat operation"}
        else:
            return {"ok": False, "error": f"Unknown operation type: {op.op}"}

    except Exception as e:
        logger.error(f"Failed to undo operation {op.op}: {e}", exc_info=True)
        return {"ok": False, "op": op.op, "error": str(e)}


def _execute_single_op(
    op: LlmOperation,
    *,
    tenant_id: str,  # noqa: ARG001
    user_id: str,
    thread_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    focus_task_id: Optional[str] = None,
    focus_action_id: Optional[str] = None,
) -> None:
    """Execute a single operation against the database.

    Args:
        op: Operation to execute
        tenant_id: Tenant identifier
        user_id: User identifier
        thread_id: Optional thread ID for ChatOp message creation
        context: Optional context dict with projects, tasks, actions
        focus_task_id: Optional focus task ID for semantic reference resolution
        focus_action_id: Optional focus action ID for semantic reference resolution
    """
    from presentation.api.repos import workroom, tasks
    from presentation.api.repos.workroom import (
        _resolve_identity,
        DuplicateProjectNameError,
        DuplicateTaskTitleError,
    )

    if isinstance(op, ChatOp):
        # Chat ops create assistant messages in the thread
        message_content = op.params.get("message", "")
        if not message_content:
            logger.warning("ChatOp missing 'message' in params, skipping")
            return

        if not thread_id:
            logger.warning(
                "ChatOp execution requires thread_id, but none provided. Skipping message creation."
            )
            return

        try:
            workroom.add_message(
                user_id=user_id,
                thread_id=thread_id,
                role="assistant",
                content=message_content,
            )
            logger.debug(f"Created assistant message in thread {thread_id}")
        except Exception as e:
            logger.error(
                f"Failed to create assistant message in thread {thread_id}: {e}",
                exc_info=True,
            )
            raise
        return

    elif isinstance(op, CreateTaskOp):
        params = op.params
        title = params.get("title", "")
        if not title:
            raise ValueError("CreateTaskOp requires 'title' in params")

        context = context or {}

        # Resolve project reference (supports "project" or "project_id" for backward compatibility)
        project_ref = params.get("project") or params.get("project_id")
        project_id = None
        if project_ref:
            try:
                project_id = _resolve_project_id(
                    project_ref, context, focus_task_id, user_id
                )
            except MultipleMatchesError as e:
                raise ValueError(str(e))
            except ValueError as e:
                raise ValueError(
                    f"{e}. Please open a chat within that project to make changes."
                )
        else:
            project_id = _get_current_project_id(context, focus_task_id, user_id)

        if not project_id:
            raise ValueError(
                "I couldn't determine which project you're working in. Please open a task inside the project you want to update."
            )

        description = params.get("description")
        priority = _normalize_enum_value(
            params.get("priority"),
            allowed=PRIORITY_VALUES,
            field="priority",
            op_type=op.op,
            default="medium",
        )

        # Resolve from_action reference (supports "from_action" or "from_action_id")
        from_action_ref = params.get("from_action") or params.get("from_action_id")
        from_action_id = None
        if from_action_ref:
            from_action_ref_str = str(from_action_ref).strip()
            if from_action_ref_str and "placeholder" not in from_action_ref_str.lower():
                try:
                    from_action_id = _resolve_action_id(
                        from_action_ref_str, context, focus_action_id, user_id
                    )
                except (ValueError, MultipleMatchesError) as e:
                    logger.warning(
                        f"Failed to resolve action reference '{from_action_ref_str}': {e}"
                    )
                    from_action_id = None

        # Convert empty strings to None
        if description is not None:
            description = (
                description.strip() if isinstance(description, str) else description
            )
            if not description:
                description = None

        workroom.create_task(
            user_id=user_id,
            title=title,
            project_id=project_id,
            importance=priority,
            description=description,
            from_action_id=from_action_id,
        )

    elif isinstance(op, UpdateTaskStatusOp):
        params = op.params
        # Resolve task reference (supports "task" or "task_id" for backward compatibility)
        task_ref = params.get("task") or params.get("task_id")
        status = _normalize_enum_value(
            params.get("status"),
            allowed=TASK_STATUS_VALUES,
            field="status",
            op_type=op.op,
            default="backlog",
        )

        if not task_ref or not status:
            raise ValueError(
                "UpdateTaskStatusOp requires ('task' or 'task_id') and 'status' in params"
            )

        try:
            task_id = _resolve_task_id(task_ref, context, focus_task_id, user_id)
        except MultipleMatchesError as e:
            raise ValueError(str(e))

        workroom.update_task_status(user_id, task_id, status)

    elif isinstance(op, LinkActionToTaskOp):
        params = op.params
        # Resolve action and task references
        action_ref = params.get("action") or params.get("action_id")
        task_ref = params.get("task") or params.get("task_id")

        if not action_ref or not task_ref:
            raise ValueError(
                "LinkActionToTaskOp requires ('action' or 'action_id') and ('task' or 'task_id') in params"
            )

        try:
            action_id = _resolve_action_id(
                action_ref, context, focus_action_id, user_id
            )
            task_id = _resolve_task_id(task_ref, context, focus_task_id, user_id)
        except MultipleMatchesError as e:
            raise ValueError(str(e))

        # Update primary link
        tasks.update_action_task_link(user_id, action_id, task_id)

        # Create join table entry
        tasks.create_task_action_link(user_id, task_id, action_id)

        # Create task_sources entry from action metadata
        try:
            action = tasks.get_action_item(user_id, action_id)
            action_source_type = action.get("source_type", "manual")
            action_source_id = action.get("source_id")
            action_payload = action.get("payload", {})
            tasks.create_task_source(
                user_id,
                task_id,
                source_type=action_source_type,
                source_id=action_source_id,
                action_id=action_id,
                metadata=action_payload,
            )
        except Exception as e:
            logger.warning(f"Failed to create task_source from action: {e}")

    elif isinstance(op, UpdateActionStateOp):
        params = op.params
        # Resolve action reference
        action_ref = params.get("action") or params.get("action_id")
        state = _normalize_enum_value(
            params.get("state"),
            allowed=ACTION_STATE_VALUES,
            field="state",
            op_type=op.op,
            default="queued",
        )

        if not action_ref or not state:
            raise ValueError(
                "UpdateActionStateOp requires ('action' or 'action_id') and 'state' in params"
            )

        try:
            action_id = _resolve_action_id(
                action_ref, context, focus_action_id, user_id
            )
        except MultipleMatchesError as e:
            raise ValueError(str(e))

        defer_until = params.get("defer_until")
        added_to_today = params.get("added_to_today")

        tasks.update_action_state(
            user_id,
            action_id,
            state=state,
            defer_until=defer_until,
            added_to_today=added_to_today,
        )

    elif isinstance(op, DeleteProjectOp):
        params = op.params
        # Resolve project references (supports "projects" or "project_ids" for backward compatibility)
        project_refs = params.get("projects") or params.get("project_ids", [])

        if not project_refs:
            raise ValueError(
                "DeleteProjectOp requires 'projects' or 'project_ids' list in params"
            )

        # Resolve all project references to UUIDs
        resolved_project_ids = []
        for ref in project_refs:
            try:
                project_id = _resolve_project_id(ref, context, focus_task_id, user_id)
                if project_id:
                    resolved_project_ids.append(project_id)
                else:
                    raise ValueError(f"Project '{ref}' not found")
            except MultipleMatchesError as e:
                raise ValueError(str(e))

        if not resolved_project_ids:
            raise ValueError("No valid projects found to delete")

        workroom.delete_projects(user_id, resolved_project_ids)

    elif isinstance(op, DeleteTaskOp):
        params = op.params
        # Resolve task references (supports "tasks" or "task_ids" for backward compatibility)
        task_refs = params.get("tasks") or params.get("task_ids", [])

        if not task_refs:
            raise ValueError(
                "DeleteTaskOp requires 'tasks' or 'task_ids' list in params"
            )

        # Resolve all task references to UUIDs
        resolved_task_ids = []
        for ref in task_refs:
            try:
                task_id = _resolve_task_id(ref, context, focus_task_id, user_id)
                resolved_task_ids.append(task_id)
            except MultipleMatchesError as e:
                raise ValueError(str(e))

        if not resolved_task_ids:
            raise ValueError("No valid tasks found to delete")

        workroom.delete_tasks(user_id, resolved_task_ids)

    else:
        raise ValueError(f"Unknown operation type: {op.op}")

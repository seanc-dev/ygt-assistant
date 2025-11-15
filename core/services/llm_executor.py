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
)

logger = logging.getLogger(__name__)

TrustMode = Literal["training_wheels", "supervised", "autonomous"]


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
        return f"I couldn't complete the requested operation: {error}. Please try again."


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
) -> Dict[str, Any]:
    """Execute LLM operations with trust gating.

    Args:
        ops: List of operations to execute
        tenant_id: Tenant identifier
        user_id: User identifier
        trust_mode: Trust level for auto-application
        thread_id: Optional thread ID for ChatOp message creation

    Returns:
        Dict with "applied", "pending", and "errors" lists
    """
    applied: List[Dict[str, Any]] = []
    pending: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []

    for op in ops:
        op_dict = {"op": op.op, "params": op.params}

        # Check if operation should be auto-applied
        if _should_apply_operation(op, trust_mode):
            try:
                _execute_single_op(op, tenant_id=tenant_id, user_id=user_id, thread_id=thread_id)
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
                if error_message and thread_id:
                    try:
                        chat_op = ChatOp(op="chat", params={"message": error_message})
                        _execute_single_op(chat_op, tenant_id=tenant_id, user_id=user_id, thread_id=thread_id)
                        applied.append({"op": "chat", "params": {"message": error_message}})
                    except Exception as chat_error:
                        logger.warning(f"Failed to generate error chat message: {chat_error}")
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
) -> Dict[str, Any]:
    """Execute a single operation that was explicitly approved by the user.

    This bypasses trust gating since the user has explicitly approved the operation.

    Args:
        op: Operation to execute
        tenant_id: Tenant identifier
        user_id: User identifier
        thread_id: Optional thread ID for ChatOp message creation

    Returns:
        Dict with operation result
    """
    try:
        _execute_single_op(op, tenant_id=tenant_id, user_id=user_id, thread_id=thread_id)
        return {"ok": True, "op": op.op, "params": op.params}
    except Exception as e:
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
                    task_ids = original_state.get("cascaded_task_ids", {}).get(project_id, [])
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
) -> None:
    """Execute a single operation against the database."""
    from presentation.api.repos import workroom, tasks

    if isinstance(op, ChatOp):
        # Chat ops create assistant messages in the thread
        message_content = op.params.get("message", "")
        if not message_content:
            logger.warning("ChatOp missing 'message' in params, skipping")
            return
        
        if not thread_id:
            logger.warning("ChatOp execution requires thread_id, but none provided. Skipping message creation.")
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
            logger.error(f"Failed to create assistant message in thread {thread_id}: {e}", exc_info=True)
            raise
        return

    elif isinstance(op, CreateTaskOp):
        params = op.params
        title = params.get("title", "")
        if not title:
            raise ValueError("CreateTaskOp requires 'title' in params")

        project_id = params.get("project_id")
        description = params.get("description")
        priority = params.get("priority", "medium")
        from_action_id = params.get("from_action_id")
        
        # Filter out placeholder values - treat as None if empty or contains "placeholder"
        if from_action_id:
            from_action_id_str = str(from_action_id).strip()
            if not from_action_id_str or "placeholder" in from_action_id_str.lower():
                from_action_id = None

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
        task_id = params.get("task_id")
        status = params.get("status")

        if not task_id or not status:
            raise ValueError(
                "UpdateTaskStatusOp requires 'task_id' and 'status' in params"
            )

        workroom.update_task_status(user_id, task_id, status)

    elif isinstance(op, LinkActionToTaskOp):
        params = op.params
        action_id = params.get("action_id")
        task_id = params.get("task_id")

        if not action_id or not task_id:
            raise ValueError(
                "LinkActionToTaskOp requires 'action_id' and 'task_id' in params"
            )

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
        action_id = params.get("action_id")
        state = params.get("state")

        if not action_id or not state:
            raise ValueError(
                "UpdateActionStateOp requires 'action_id' and 'state' in params"
            )

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
        project_ids = params.get("project_ids", [])
        
        if not project_ids:
            raise ValueError("DeleteProjectOp requires 'project_ids' list in params")
        
        workroom.delete_projects(user_id, project_ids)

    elif isinstance(op, DeleteTaskOp):
        params = op.params
        task_ids = params.get("task_ids", [])
        
        if not task_ids:
            raise ValueError("DeleteTaskOp requires 'task_ids' list in params")
        
        workroom.delete_tasks(user_id, task_ids)

    else:
        raise ValueError(f"Unknown operation type: {op.op}")

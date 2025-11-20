"""Supabase-backed repositories for the Workroom experience."""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

import httpx

from archive.infra.supabase.client import client
from settings import TENANT_DEFAULT

logger = logging.getLogger(__name__)

DEV_USER_EMAIL = os.getenv("DEV_USER_EMAIL", "test.user+local@example.com")


class DuplicateProjectNameError(Exception):
    """Raised when attempting to create a project with a name that already exists."""
    pass


class DuplicateTaskTitleError(Exception):
    """Raised when attempting to create a task with a title that already exists in the project."""
    pass


def get_projects(user_id: str) -> List[Dict[str, Any]]:
    """Fetch all projects scoped to the caller's tenant (excluding deleted)."""
    tenant_id, _ = _resolve_identity(user_id)
    params = {
        "tenant_id": f"eq.{tenant_id}",
        "order": "order_index.asc",
    }
    rows = _select("projects", params)
    # Filter deleted projects in Python; this works whether or not the column exists.
    rows = [r for r in rows if r.get("deleted_at") is None]
    rows.sort(key=lambda r: (r.get("order_index") or 0, r.get("created_at") or ""))
    return rows


def get_tasks(user_id: str, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetch all tasks (optionally filtered by project) for the caller's tenant (excluding deleted)."""
    tenant_id, _ = _resolve_identity(user_id)
    params: Dict[str, Any] = {
        "tenant_id": f"eq.{tenant_id}",
        "order": "created_at.desc",
    }
    if project_id:
        params["project_id"] = f"eq.{project_id}"
    rows = _select("tasks", params)
    return [r for r in rows if r.get("deleted_at") is None]


def get_threads(user_id: str, task_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetch chat threads scoped to the tenant."""
    tenant_id, _ = _resolve_identity(user_id)
    params: Dict[str, Any] = {
        "tenant_id": f"eq.{tenant_id}",
        "order": "updated_at.desc",
    }
    if task_id:
        params["task_id"] = f"eq.{task_id}"

    threads = _select("threads", params)
    for thread in threads:
        thread.setdefault("messages", [])
    return threads


def create_project(
    user_id: str, name: str, description: Optional[str] = None, priority: str = "medium"
) -> Dict[str, Any]:
    """Create a project row in Supabase.
    
    Raises:
        DuplicateProjectNameError: If a project with the same name (case-insensitive) already exists for this tenant.
    """
    tenant_id, resolved_user_id = _resolve_identity(user_id)
    
    # Check for duplicate project name (case-insensitive)
    existing_projects = get_projects(user_id)
    name_lower = name.lower().strip()
    for project in existing_projects:
        if project.get("name", "").lower().strip() == name_lower:
            raise DuplicateProjectNameError(
                f"Project '{name}' already exists. Would you like to name it something else?"
            )
    
    payload = {
        "tenant_id": tenant_id,
        "owner_id": resolved_user_id,
        "name": name,
        "description": description,
        "priority": priority,
        "metadata": {},
    }
    return _insert("projects", payload)


def create_task(
    user_id: str,
    title: str,
    project_id: Optional[str] = None,
    status: str = "backlog",
    importance: str = "medium",
    due: Optional[str] = None,
    description: Optional[str] = None,
    from_action_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a task row in Supabase.

    Args:
        user_id: User identifier
        title: Task title
        project_id: Optional project ID
        status: Task status (default: "backlog")
        importance: Priority level (default: "medium")
        due: Optional due date ISO string
        description: Optional task description
        from_action_id: Optional action ID that this task is created from
    
    Raises:
        DuplicateTaskTitleError: If a task with the same title (case-insensitive) already exists in the project.
    """
    tenant_id, resolved_user_id = _resolve_identity(user_id)
    
    # Check for duplicate task title within the project (case-insensitive)
    if project_id:
        existing_tasks = get_tasks(user_id, project_id=project_id)
        title_lower = title.lower().strip()
        for task in existing_tasks:
            if task.get("title", "").lower().strip() == title_lower:
                # Get project name for error message
                projects = get_projects(user_id)
                project_name = next((p.get("name", "this project") for p in projects if p.get("id") == project_id), "this project")
                raise DuplicateTaskTitleError(
                    f"This project already has a task with that name. Would you like to name it something else?"
                )
    
    payload = {
        "tenant_id": tenant_id,
        "owner_id": resolved_user_id,
        "title": title,
        "status": status,
        "priority": importance,
        "due_at": due,
        "source_type": "manual",
        "source_ref": {},
    }
    if project_id:
        payload["project_id"] = project_id
    if description:
        payload["description"] = description
    task = _insert("tasks", payload)

    # If from_action_id is provided, link the action to the task
    if from_action_id:
        # Filter out placeholder values
        from_action_id_str = str(from_action_id).strip()
        if from_action_id_str and "placeholder" not in from_action_id_str.lower():
            from presentation.api.repos import tasks as tasks_repo

            try:
                tasks_repo.update_action_task_link(user_id, from_action_id, task["id"])
                # Create task_action_links entry (many-to-many join)
                tasks_repo.create_task_action_link(user_id, task["id"], from_action_id)
                # Create task_sources entry from action metadata
                try:
                    action = tasks_repo.get_action_item(user_id, from_action_id)
                    action_source_type = action.get("source_type", "manual")
                    action_source_id = action.get("source_id")
                    action_payload = action.get("payload", {})
                    tasks_repo.create_task_source(
                        user_id,
                        task["id"],
                        source_type=action_source_type,
                        source_id=action_source_id,
                        action_id=from_action_id,
                        metadata=action_payload,
                    )
                except ValueError:
                    # Action doesn't exist - skip linking (likely placeholder from LLM)
                    logger.debug(
                        f"Skipping action link - action {from_action_id} not found"
                    )
                except Exception as e:
                    logger.warning(f"Failed to create task_source from action: {e}")
            except ValueError:
                # Action doesn't exist - skip linking
                logger.debug(
                    f"Skipping action link - action {from_action_id} not found"
                )
            except Exception as e:
                logger.warning(f"Failed to link action to task: {e}")

    return task


def create_thread(
    user_id: str,
    task_id: Optional[str] = None,
    title: Optional[str] = None,
    prefs: Optional[Dict[str, Any]] = None,
    source_action_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a chat thread tied to a task or source action.

    Note: Requires database schema with 'prefs' and 'context_refs' columns in threads table.
    Ensure migration 20251114000000_baseline.sql (not 20251114T000000_baseline.sql) is applied.
    """
    tenant_id, resolved_user_id = _resolve_identity(user_id)
    payload = {
        "tenant_id": tenant_id,
        "task_id": task_id,
        "source_action_id": source_action_id,
        "title": title or "Untitled Thread",
        "created_by": resolved_user_id,
        "prefs": prefs or {},
        "context_refs": [],
    }
    thread = _insert("threads", payload)
    thread["messages"] = []
    return thread


def update_task_status(user_id: str, task_id: str, status: str) -> Dict[str, Any]:
    """Update status for a single task row."""
    tenant_id, _ = _resolve_identity(user_id)
    return _patch(
        "tasks",
        {"tenant_id": f"eq.{tenant_id}", "id": f"eq.{task_id}"},
        {"status": status},
    )


def get_task(user_id: str, task_id: str) -> Dict[str, Any]:
    """Load a single task for the caller's tenant (excluding deleted)."""
    tenant_id, _ = _resolve_identity(user_id)
    params = {
        "tenant_id": f"eq.{tenant_id}",
        "id": f"eq.{task_id}",
    }
    task = _select_one("tasks", params)
    if task.get("deleted_at") is not None:
        raise ValueError(f"Task {task_id} is deleted")
    return task


def get_thread(user_id: str, thread_id: str) -> Dict[str, Any]:
    """Load a thread and its messages."""
    tenant_id, _ = _resolve_identity(user_id)
    thread = _select_one(
        "threads", {"tenant_id": f"eq.{tenant_id}", "id": f"eq.{thread_id}"}
    )
    messages = _select(
        "messages",
        {
            "tenant_id": f"eq.{tenant_id}",
            "thread_id": f"eq.{thread_id}",
            "order": "created_at.asc",
        },
    )
    for message in messages:
        message["ts"] = message.get("created_at")
    thread["messages"] = messages
    return thread


def add_message(
    user_id: str,
    thread_id: str,
    role: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Insert a message and update the thread timestamp."""
    tenant_id, resolved_user_id = _resolve_identity(user_id)
    # Ensure thread exists within tenant scope
    _select_one("threads", {"tenant_id": f"eq.{tenant_id}", "id": f"eq.{thread_id}"})
    payload = {
        "tenant_id": tenant_id,
        "thread_id": thread_id,
        "user_id": resolved_user_id if role == "user" else None,
        "role": role,
        "content": content,
        "metadata": metadata or {},
    }
    message = _insert("messages", payload)
    message["ts"] = message.get("created_at")
    return message


def get_pending_user_messages(
    thread_id: str,
    user_id: str,
) -> List[Dict[str, Any]]:
    """Get all user messages since the last assistant response.

    Args:
        thread_id: Thread identifier
        user_id: User identifier

    Returns:
        List of user messages (dicts with id, role, content, ts/created_at)
    """
    tenant_id, _ = _resolve_identity(user_id)

    # Get all messages for the thread
    all_messages = _select(
        "messages",
        {
            "tenant_id": f"eq.{tenant_id}",
            "thread_id": f"eq.{thread_id}",
            "order": "created_at.asc",
        },
    )

    if not all_messages:
        return []

    # Find the last assistant message timestamp
    last_assistant_ts = None
    for msg in reversed(all_messages):
        if msg.get("role") == "assistant":
            last_assistant_ts = msg.get("created_at") or msg.get("ts")
            break

    # If no assistant message exists, return all user messages
    if last_assistant_ts is None:
        return [msg for msg in all_messages if msg.get("role") == "user"]

    # Return all user messages after the last assistant message
    pending = []
    for msg in all_messages:
        msg_ts = msg.get("created_at") or msg.get("ts")
        if msg.get("role") == "user" and msg_ts and msg_ts > last_assistant_ts:
            pending.append(msg)

    return pending


def get_recent_assistant_messages(
    user_id: str, limit: int = 20
) -> List[Dict[str, Any]]:
    """Fetch recent assistant messages for the caller's tenant."""
    tenant_id, _ = _resolve_identity(user_id)
    params: Dict[str, Any] = {
        "tenant_id": f"eq.{tenant_id}",
        "role": "eq.assistant",
        "order": "created_at.desc",
        "limit": str(limit),
    }
    return _select("messages", params)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _resolve_identity(user_id: Optional[str]) -> Tuple[str, str]:
    """Map incoming user identifier to a Supabase user + tenant."""
    row: Optional[Dict[str, Any]] = None
    if user_id:
        if _looks_like_uuid(user_id):
            row = _fetch_user({"id": f"eq.{user_id}"})
        elif "@" in user_id:
            row = _fetch_user({"email": f"eq.{user_id}"})
    if not row and DEV_USER_EMAIL:
        row = _fetch_user({"email": f"eq.{DEV_USER_EMAIL}"})
    if not row:
        row = _fetch_user({})
    if not row:
        raise RuntimeError("No workroom users provisioned in Supabase.")
    tenant_id = row.get("tenant_id") or TENANT_DEFAULT
    return tenant_id, row["id"]


def _fetch_user(filters: Dict[str, str]) -> Optional[Dict[str, Any]]:
    params: Dict[str, Any] = {"limit": "1", "order": "created_at.asc"}
    params.update(filters)
    rows = _select("users", params)
    return rows[0] if rows else None


def _looks_like_uuid(value: str) -> bool:
    try:
        UUID(value)
        return True
    except Exception:
        return False


def _select(
    table: str, params: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """Select rows from a table with PostgREST query parameters.

    Handles deleted_at filtering gracefully - if the column doesn't exist
    or PostgREST rejects the filter, falls back to Python-side filtering.
    """
    qp = dict(params or {})
    qp.setdefault("select", "*")
    # Separate order from filters to avoid PostgREST parsing issues
    order_param = qp.pop("order", None)
    with client() as c:
        # Build query params manually to ensure proper encoding
        query_params = {}
        for key, value in qp.items():
            query_params[key] = value
        if order_param:
            query_params["order"] = order_param
        resp = c.get(f"/{table}", params=query_params)
        resp.raise_for_status()
        return resp.json()


def _select_one(table: str, params: Dict[str, Any]) -> Dict[str, Any]:
    qp = dict(params)
    qp["limit"] = "1"
    rows = _select(table, qp)
    if not rows:
        raise ValueError(f"{table} not found for filters {params}")
    return rows[0]


def _insert(table: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Insert a row and return the created record.

    Raises RuntimeError if the insert fails or returns unexpected data.
    """
    with client() as c:
        resp = c.post(
            f"/{table}",
            json=payload,
            headers={"Prefer": "return=representation"},
        )
        resp.raise_for_status()

        try:
            data = resp.json()
        except Exception as e:
            logger.error(
                f"Failed to parse JSON response from {table} insert",
                extra={
                    "table": table,
                    "payload": payload,
                    "error": str(e),
                    "status_code": resp.status_code,
                },
            )
            raise RuntimeError(f"Failed to parse response from {table} insert: {e}")

        # Handle both list and single object responses
        if isinstance(data, list):
            if not data:
                logger.error(
                    f"Insert to {table} returned empty response",
                    extra={"table": table, "payload": payload, "response": data},
                )
                raise RuntimeError(
                    f"Insert to {table} returned empty response. "
                    f"This usually indicates a database constraint violation or RLS policy issue. "
                    f"Payload: {payload}"
                )
            row = data[0]
        elif isinstance(data, dict):
            row = data
        else:
            logger.error(
                f"Unexpected response format from {table} insert",
                extra={
                    "table": table,
                    "payload": payload,
                    "response_type": type(data).__name__,
                    "response": data,
                },
            )
            raise RuntimeError(
                f"Unexpected response format from {table} insert: {type(data)}. "
                f"Expected list or dict, got {type(data).__name__}"
            )

        # Validate required fields
        if "id" not in row:
            logger.error(
                f"Insert to {table} succeeded but response missing 'id' field",
                extra={"table": table, "payload": payload, "response": row},
            )
            raise RuntimeError(
                f"Insert to {table} succeeded but response missing 'id' field. "
                f"Response: {row}"
            )

        if "created_at" not in row:
            logger.warning(
                f"Insert to {table} succeeded but response missing 'created_at' field",
                extra={"table": table, "payload": payload, "response": row},
            )

        logger.debug(
            f"Successfully inserted row into {table}",
            extra={"table": table, "id": row.get("id")},
        )

        return row


def _patch(
    table: str, filters: Dict[str, str], payload: Dict[str, Any]
) -> Dict[str, Any]:
    with client() as c:
        resp = c.patch(
            f"/{table}",
            params=filters,
            json=payload,
            headers={"Prefer": "return=representation"},
        )
        resp.raise_for_status()
        data = resp.json()
        if not data:
            raise ValueError(f"{table} not found for filters {filters}")
        return data[0] if isinstance(data, list) else data


def delete_project(user_id: str, project_id: str) -> Dict[str, Any]:
    """Soft delete a project and cascade delete all tasks in the project.

    Args:
        user_id: User identifier
        project_id: Project ID to delete

    Returns:
        Dict with deleted project and count of deleted tasks
    """
    from datetime import datetime, timezone

    tenant_id, _ = _resolve_identity(user_id)
    deleted_at = datetime.now(timezone.utc).isoformat()

    # Verify project exists and belongs to tenant (not deleted)
    project = _select_one(
        "projects", {"tenant_id": f"eq.{tenant_id}", "id": f"eq.{project_id}"}
    )
    if project.get("deleted_at") is not None:
        raise ValueError(f"Project {project_id} is already deleted")

    # Soft delete the project
    _patch(
        "projects",
        {"tenant_id": f"eq.{tenant_id}", "id": f"eq.{project_id}"},
        {"deleted_at": deleted_at},
    )

    # Cascade: soft delete all tasks in the project
    tasks_to_delete = _select(
        "tasks",
        {
            "tenant_id": f"eq.{tenant_id}",
            "project_id": f"eq.{project_id}",
        },
    )
    tasks_to_delete = [t for t in tasks_to_delete if t.get("deleted_at") is None]

    task_count = 0
    for task in tasks_to_delete:
        try:
            _patch(
                "tasks",
                {"tenant_id": f"eq.{tenant_id}", "id": f"eq.{task['id']}"},
                {"deleted_at": deleted_at},
            )
            task_count += 1
        except Exception as e:
            logger.warning(f"Failed to delete task {task['id']}: {e}")

    return {
        "project": project,
        "tasks_deleted": task_count,
        "deleted_at": deleted_at,
    }


def delete_projects(user_id: str, project_ids: List[str]) -> Dict[str, Any]:
    """Soft delete multiple projects and cascade delete their tasks.

    Args:
        user_id: User identifier
        project_ids: List of project IDs to delete

    Returns:
        Dict with summary: total projects deleted, total tasks deleted
    """
    total_projects = 0
    total_tasks = 0
    deleted_projects = []

    for project_id in project_ids:
        try:
            result = delete_project(user_id, project_id)
            total_projects += 1
            total_tasks += result.get("tasks_deleted", 0)
            deleted_projects.append(result["project"])
        except ValueError as e:
            logger.warning(f"Project {project_id} not found or already deleted: {e}")
        except Exception as e:
            logger.error(f"Failed to delete project {project_id}: {e}", exc_info=True)

    return {
        "projects_deleted": total_projects,
        "tasks_deleted": total_tasks,
        "projects": deleted_projects,
    }


def delete_task(user_id: str, task_id: str) -> Dict[str, Any]:
    """Soft delete a task.

    Args:
        user_id: User identifier
        task_id: Task ID to delete

    Returns:
        Dict with deleted task
    """
    from datetime import datetime, timezone

    tenant_id, _ = _resolve_identity(user_id)
    deleted_at = datetime.now(timezone.utc).isoformat()

    # Verify task exists and belongs to tenant (not deleted)
    task = _select_one("tasks", {"tenant_id": f"eq.{tenant_id}", "id": f"eq.{task_id}"})
    if task.get("deleted_at") is not None:
        raise ValueError(f"Task {task_id} is already deleted")

    # Soft delete the task
    _patch(
        "tasks",
        {"tenant_id": f"eq.{tenant_id}", "id": f"eq.{task_id}"},
        {"deleted_at": deleted_at},
    )

    return {
        "task": task,
        "deleted_at": deleted_at,
    }


def delete_tasks(user_id: str, task_ids: List[str]) -> Dict[str, Any]:
    """Soft delete multiple tasks.

    Args:
        user_id: User identifier
        task_ids: List of task IDs to delete

    Returns:
        Dict with summary: total tasks deleted
    """
    total_tasks = 0
    deleted_tasks = []

    for task_id in task_ids:
        try:
            result = delete_task(user_id, task_id)
            total_tasks += 1
            deleted_tasks.append(result["task"])
        except ValueError as e:
            logger.warning(f"Task {task_id} not found or already deleted: {e}")
        except Exception as e:
            logger.error(f"Failed to delete task {task_id}: {e}", exc_info=True)

    return {
        "tasks_deleted": total_tasks,
        "tasks": deleted_tasks,
    }

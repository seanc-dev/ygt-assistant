"""Workroom endpoints."""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Request, Depends, HTTPException
from pydantic import BaseModel, Field
from presentation.api.repos import workroom as workroom_repo, audit_log
from presentation.api.routes.queue import _get_user_id
from datetime import datetime, timezone
import uuid
import os
import asyncio

router = APIRouter()

# Thread-level lock to prevent concurrent assistant response generation
_assistant_lock: Dict[str, asyncio.Lock] = {}
_lock_lock = asyncio.Lock()  # Lock for managing the lock dictionary


async def _get_thread_lock(thread_id: str) -> asyncio.Lock:
    """Get or create a lock for a specific thread."""
    async with _lock_lock:
        if thread_id not in _assistant_lock:
            _assistant_lock[thread_id] = asyncio.Lock()
        return _assistant_lock[thread_id]


# Feature flag for seeding threads
FEATURE_SEED_THREADS = os.getenv("FEATURE_SEED_THREADS", "false").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}


def _normalize_task_status(status: str) -> str:
    """Normalize task status to match database enum values.

    Maps frontend-friendly values to database enum values:
    - "todo" -> "backlog" (database enum doesn't include "todo")
    """
    status_map = {
        "todo": "backlog",
    }
    return status_map.get(status.lower(), status.lower())


DEV_MODE = os.getenv("DEV_MODE", "false").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
USE_MOCK_GRAPH = os.getenv("USE_MOCK_GRAPH", "true").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}

# Seed messages for demo threads
SEED_MESSAGES = [
    {
        "role": "assistant",
        "content": "I've read the email. Want me to draft a response summarizing your budget concerns?",
    },
    {
        "role": "user",
        "content": "Yes. Keep it concise and ask for the revised figures.",
    },
    {
        "role": "assistant",
        "content": "Draft ready. Would you like to send or edit?",
    },
]


def _generate_dev_response(user_message: str) -> str:
    """Generate a dev-only automatic assistant response.

    This is a simple pattern-based response generator for dev/testing.
    In production, this would call an actual LLM API.
    """
    user_lower = user_message.lower()

    # Pattern-based responses
    if any(word in user_lower for word in ["hello", "hi", "hey"]):
        return "Hello! How can I help you today?"
    elif any(word in user_lower for word in ["thanks", "thank", "appreciate"]):
        return "You're welcome! Is there anything else you'd like me to help with?"
    elif any(
        word in user_lower for word in ["yes", "yeah", "yep", "sure", "ok", "okay"]
    ):
        return "Great! I'll take care of that for you."
    elif any(word in user_lower for word in ["no", "nope", "nah"]):
        return "Understood. Let me know if you change your mind."
    elif any(word in user_lower for word in ["draft", "write", "create", "make"]):
        return "I've drafted that for you. Would you like to review it before sending?"
    elif any(word in user_lower for word in ["schedule", "meeting", "calendar"]):
        return "I can help you schedule that. What time works best for you?"
    elif any(word in user_lower for word in ["follow up", "follow-up"]):
        return "I'll follow up on that. Should I include any specific details?"
    elif "?" in user_message:
        return "That's a good question. Let me think about the best approach here."
    else:
        # Generic helpful response
        return (
            "I understand. I can help you with that. What would you like me to do next?"
        )


class CreateThreadRequest(BaseModel):
    task_id: Optional[str] = Field(None, description="Task ID to create thread under")
    title: str = Field(..., description="Thread title")
    prefs: Optional[Dict[str, Any]] = Field(
        default=None, description="Thread preferences"
    )
    source_action_id: Optional[str] = Field(
        None, description="Action ID to create thread from"
    )


class SendMessageRequest(BaseModel):
    role: str = Field(..., description="user|assistant")
    content: str = Field(..., description="Message content")


class UpdateTaskStatusRequest(BaseModel):
    status: str = Field(..., description="todo|doing|done|blocked")


@router.get("/api/workroom/tree")
async def workroom_tree(
    request: Request,
    user_id: str = Depends(_get_user_id),
) -> Dict[str, Any]:
    """Get project/task/thread hierarchy.

    Returns tree structure: Project → Task → Threads.
    """
    projects = workroom_repo.get_projects(user_id)
    tasks = workroom_repo.get_tasks(user_id)
    threads = workroom_repo.get_threads(user_id)

    # Build tree structure
    tree = []
    for project in projects:
        project_tasks = [t for t in tasks if t.get("project_id") == project["id"]]

        # Add threads to each task
        for task in project_tasks:
            task_threads = [t for t in threads if t.get("task_id") == task["id"]]
            task["children"] = task_threads

        project["children"] = project_tasks
        tree.append(project)

    return {
        "ok": True,
        "tree": tree,
    }


@router.post("/api/workroom/thread")
async def create_thread(
    body: CreateThreadRequest,
    request: Request,
    user_id: str = Depends(_get_user_id),
    seed: bool = False,
) -> Dict[str, Any]:
    """Create a new thread.

    Creates a new thread under a task, or from an action if source_action_id is provided.

    If seed=true or FEATURE_SEED_THREADS is enabled and DEV_MODE/USE_MOCK_GRAPH are true,
    seeds the thread with demo messages.
    """
    # If source_action_id is provided, we can create a thread without a task
    if body.source_action_id:
        # Create thread from action
        thread = workroom_repo.create_thread(
            user_id=user_id,
            title=body.title,
            prefs=body.prefs,
            source_action_id=body.source_action_id,
        )
    else:
        # Verify task exists
        if not body.task_id:
            raise HTTPException(
                status_code=400,
                detail="Either task_id or source_action_id must be provided",
            )
        try:
            task = workroom_repo.get_task(user_id, body.task_id)
        except ValueError:
            raise HTTPException(status_code=404, detail="Task not found")

        # Create thread
        thread = workroom_repo.create_thread(
            user_id=user_id,
            task_id=body.task_id,
            title=body.title,
            prefs=body.prefs,
        )

    # Seed messages if enabled - always seed in dev mode for action cards
    should_seed = seed or (DEV_MODE and body.source_action_id)
    if should_seed:
        from datetime import timezone

        for msg_data in SEED_MESSAGES:
            workroom_repo.add_message(
                user_id=user_id,
                thread_id=thread["id"],
                role=msg_data["role"],
                content=msg_data["content"],
            )

    # Audit log
    request_id = getattr(request.state, "request_id", None)
    audit_log.write_audit(
        "create_thread",
        {
            "user_id": user_id,
            "thread_id": thread["id"],
            "task_id": thread.get("task_id"),
            "source_action_id": body.source_action_id,
            "title": body.title,
            "seeded": should_seed,
        },
        request_id=request_id,
    )

    return {
        "ok": True,
        "thread": thread,
    }


@router.get("/api/workroom/projects")
async def get_projects(
    request: Request,
    user_id: str = Depends(_get_user_id),
) -> Dict[str, Any]:
    """Get all projects for the user."""
    try:
        projects = workroom_repo.get_projects(user_id)
        # Transform to match frontend schema
        transformed = [
            {
                "id": p["id"],
                "title": p["name"],
                "brief": p.get("description"),
                "createdAt": p.get(
                    "created_at", datetime.now(timezone.utc).isoformat()
                ),
                "updatedAt": p.get(
                    "updated_at",
                    p.get("created_at", datetime.now(timezone.utc).isoformat()),
                ),
            }
            for p in projects
        ]
        return {"ok": True, "projects": transformed}
    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error loading projects: {str(e)}")


@router.get("/api/workroom/projects/{project_id}")
async def get_project(
    project_id: str,
    request: Request,
    user_id: str = Depends(_get_user_id),
) -> Dict[str, Any]:
    """Get a single project."""
    projects = workroom_repo.get_projects(user_id)
    project = next((p for p in projects if p["id"] == project_id), None)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return {
        "ok": True,
        "project": {
            "id": project["id"],
            "title": project["name"],
            "brief": project.get("description"),
            "createdAt": project.get(
                "created_at", datetime.now(timezone.utc).isoformat()
            ),
            "updatedAt": project.get(
                "updated_at",
                project.get("created_at", datetime.now(timezone.utc).isoformat()),
            ),
        },
    }


@router.post("/api/workroom/projects")
async def create_project(
    body: Dict[str, Any],
    request: Request,
    user_id: str = Depends(_get_user_id),
) -> Dict[str, Any]:
    """Create a new project."""
    project = workroom_repo.create_project(
        user_id=user_id,
        name=body.get("title", "Untitled Project"),
        description=body.get("brief"),
    )
    return {
        "ok": True,
        "project": {
            "id": project["id"],
            "title": project["name"],
            "brief": project.get("description"),
            "createdAt": project.get("created_at"),
            "updatedAt": project.get("updated_at", project.get("created_at")),
        },
    }


@router.get("/api/workroom/projects/{project_id}/tasks")
async def get_tasks(
    project_id: str,
    request: Request,
    user_id: str = Depends(_get_user_id),
) -> Dict[str, Any]:
    """Get all tasks for a project."""
    tasks = workroom_repo.get_tasks(user_id, project_id=project_id)
    # Transform to match frontend schema
    threads = workroom_repo.get_threads(user_id)
    transformed = []
    for task in tasks:
        task_threads = [t for t in threads if t.get("task_id") == task["id"]]
        transformed.append(
            {
                "id": task["id"],
                "projectId": task["project_id"],
                "title": task["title"],
                "status": task["status"],
                "priority": task.get("importance"),
                "due": task.get("due"),
                "tags": [],
                "doc": None,  # TODO: Add doc support
                "chats": [
                    {
                        "id": t["id"],
                        "title": t["title"],
                        "pinned": False,
                        "lastMessageAt": t.get("updated_at"),
                    }
                    for t in task_threads
                ],
                "unreadCount": 0,
                "createdAt": task.get(
                    "created_at", datetime.now(timezone.utc).isoformat()
                ),
                "updatedAt": task.get(
                    "updated_at",
                    task.get("created_at", datetime.now(timezone.utc).isoformat()),
                ),
            }
        )
    return {"ok": True, "tasks": transformed}


@router.get("/api/workroom/tasks/{task_id}")
async def get_task(
    task_id: str,
    request: Request,
    user_id: str = Depends(_get_user_id),
) -> Dict[str, Any]:
    """Get a single task."""
    from datetime import timezone

    try:
        task = workroom_repo.get_task(user_id, task_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Task not found")

    threads = workroom_repo.get_threads(user_id, task_id=task_id)
    return {
        "ok": True,
        "task": {
            "id": task["id"],
            "projectId": task["project_id"],
            "title": task["title"],
            "status": task["status"],
            "priority": task.get("importance"),
            "due": task.get("due"),
            "tags": [],
            "doc": None,
            "chats": [
                {
                    "id": t["id"],
                    "title": t["title"],
                    "pinned": False,
                    "lastMessageAt": t.get("updated_at"),
                }
                for t in threads
            ],
            "unreadCount": 0,
            "createdAt": task.get("created_at", datetime.now(timezone.utc).isoformat()),
            "updatedAt": task.get(
                "updated_at",
                task.get("created_at", datetime.now(timezone.utc).isoformat()),
            ),
        },
    }


@router.post("/api/workroom/tasks")
async def create_task(
    body: Dict[str, Any],
    request: Request,
    user_id: str = Depends(_get_user_id),
) -> Dict[str, Any]:
    """Create a new task."""
    from datetime import timezone

    # Normalize status to match database enum (map "todo" to "backlog")
    raw_status = body.get("status", "backlog")
    normalized_status = _normalize_task_status(raw_status)

    task = workroom_repo.create_task(
        user_id=user_id,
        project_id=body["projectId"],
        title=body["title"],
        status=normalized_status,
        importance=body.get("priority", "medium"),
        due=body.get("due"),
    )
    return {
        "ok": True,
        "task": {
            "id": task["id"],
            "projectId": task["project_id"],
            "title": task["title"],
            "status": task["status"],
            "priority": task.get("importance"),
            "due": task.get("due"),
            "tags": [],
            "doc": None,
            "chats": [],
            "unreadCount": 0,
            "createdAt": task.get("created_at"),
            "updatedAt": task.get("updated_at", task.get("created_at")),
        },
    }


@router.patch("/api/workroom/tasks/{task_id}/status")
async def update_task_status(
    task_id: str,
    body: UpdateTaskStatusRequest,
    request: Request,
    user_id: str = Depends(_get_user_id),
) -> Dict[str, Any]:
    """Update task status.

    Valid statuses: backlog, ready, doing, blocked, done, todo
    Note: "todo" is mapped to "backlog" for database storage.
    """
    valid_statuses = ["backlog", "ready", "doing", "blocked", "done", "todo"]
    if body.status not in valid_statuses:
        raise HTTPException(
            status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}"
        )

    # Normalize status to match database enum (map "todo" to "backlog")
    normalized_status = _normalize_task_status(body.status)

    try:
        task = workroom_repo.update_task_status(user_id, task_id, normalized_status)
    except ValueError:
        raise HTTPException(status_code=404, detail="Task not found")

    # Audit log (use original status for audit, not normalized)
    request_id = getattr(request.state, "request_id", None)
    audit_log.write_audit(
        "update_task_status",
        {
            "user_id": user_id,
            "task_id": task_id,
            "status": body.status,  # Original status from request
            "normalized_status": normalized_status,  # Actual status stored in DB
        },
        request_id=request_id,
    )

    return {
        "ok": True,
        "task": task,
    }


@router.get("/api/workroom/tasks/{task_id}/doc")
async def get_task_doc(
    task_id: str,
    request: Request,
    user_id: str = Depends(_get_user_id),
) -> Dict[str, Any]:
    """Get task doc."""
    # TODO: Implement doc storage
    return {"ok": True, "doc": None}


@router.put("/api/workroom/tasks/{task_id}/doc")
async def update_task_doc(
    task_id: str,
    body: Dict[str, Any],
    request: Request,
    user_id: str = Depends(_get_user_id),
) -> Dict[str, Any]:
    """Update task doc."""
    # TODO: Implement doc storage
    return {
        "ok": True,
        "doc": {
            "id": str(uuid.uuid4()),
            "contentJSON": body.get("contentJSON", {}),
            "updatedAt": datetime.now(timezone.utc).isoformat(),
        },
    }


@router.get("/api/workroom/tasks/{task_id}/chats")
async def get_task_chats(
    task_id: str,
    request: Request,
    user_id: str = Depends(_get_user_id),
) -> Dict[str, Any]:
    """Get chats for a task."""
    threads = workroom_repo.get_threads(user_id, task_id=task_id)
    chats = [
        {
            "id": t["id"],
            "title": t["title"],
            "pinned": False,
            "lastMessageAt": t.get("updated_at"),
        }
        for t in threads
    ]
    return {"ok": True, "chats": chats}


@router.post("/api/workroom/tasks/{task_id}/chats")
async def create_task_chat(
    task_id: str,
    body: Dict[str, Any],
    request: Request,
    user_id: str = Depends(_get_user_id),
) -> Dict[str, Any]:
    """Create a new chat for a task."""
    thread = workroom_repo.create_thread(
        user_id=user_id,
        task_id=task_id,
        title=body.get("title", "New Chat"),
    )
    return {
        "ok": True,
        "chat": {
            "id": thread["id"],
            "title": thread["title"],
            "pinned": False,
            "lastMessageAt": thread.get("created_at"),
        },
    }


@router.get("/api/workroom/thread/{thread_id}")
async def get_thread(
    thread_id: str,
    request: Request,
    user_id: str = Depends(_get_user_id),
    limit: int = 30,
    before: Optional[str] = None,
) -> Dict[str, Any]:
    """Get a thread with messages.

    Supports pagination via limit and before cursor.
    """
    try:
        thread = workroom_repo.get_thread(user_id, thread_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Thread not found")

    # Get messages (for now, return all; pagination can be added later)
    messages = thread.get("messages", [])
    if before:
        # Simple pagination: find message with id == before and return messages before it
        before_idx = next(
            (i for i, msg in enumerate(messages) if msg["id"] == before), len(messages)
        )
        messages = messages[:before_idx]

    messages = messages[-limit:] if limit else messages

    return {
        "ok": True,
        "thread": {
            "id": thread["id"],
            "title": thread.get("title"),
            "messages": messages,
        },
    }


@router.post("/api/workroom/thread/{thread_id}/message")
async def send_message(
    thread_id: str,
    body: SendMessageRequest,
    request: Request,
    user_id: str = Depends(_get_user_id),
) -> Dict[str, Any]:
    """Send a message to a thread.

    Valid roles: user, assistant
    """
    if body.role not in ["user", "assistant"]:
        raise HTTPException(
            status_code=400, detail="Invalid role. Must be 'user' or 'assistant'"
        )

    try:
        message = workroom_repo.add_message(
            user_id=user_id,
            thread_id=thread_id,
            role=body.role,
            content=body.content,
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="Thread not found")

    # Audit log
    request_id = getattr(request.state, "request_id", None)
    audit_log.write_audit(
        "send_message",
        {
            "user_id": user_id,
            "thread_id": thread_id,
            "message_id": message["id"],
            "role": body.role,
        },
        request_id=request_id,
    )

    return {
        "ok": True,
        "message": message,
    }


@router.post("/dev/workroom/seed")
async def seed_workroom(
    request: Request,
    user_id: str = Depends(_get_user_id),
) -> Dict[str, Any]:
    """Seed workroom with test data (dev only)."""
    if not DEV_MODE:
        raise HTTPException(
            status_code=403, detail="Seed endpoint only available in dev mode"
        )

    # Always use mock DB when available (for testing, independent of LLM_TESTING_MODE)
    import os

    try:
        from llm_testing.mock_db import get_mock_client
        from presentation.api.repos.workroom import _resolve_identity

        tenant_id, resolved_user_id = _resolve_identity(user_id)
        mock_db = get_mock_client()
        # Check if mock DB is actually being used (has seeded user)
        if mock_db._tables.get("users"):
            seed_data = mock_db.seed_workroom(resolved_user_id, tenant_id)
            # Return in same format as real seeding
            return {
                "ok": True,
                "projects": len(seed_data["projects"]),
                "tasks": len(seed_data["tasks"]),
                "threads": 0,
            }
    except Exception as e:
        # Fall through to real seeding if mock fails or not available
        import logging

        logging.getLogger(__name__).debug(f"Mock DB not available, using real DB: {e}")

    # Create projects
    project1 = workroom_repo.create_project(
        user_id=user_id,
        name="Product Launch",
        description="Q4 product launch planning and execution",
    )
    project2 = workroom_repo.create_project(
        user_id=user_id,
        name="Marketing Campaign",
        description="Social media and email marketing campaign",
    )

    # Create tasks
    task1 = workroom_repo.create_task(
        user_id=user_id,
        project_id=project1["id"],
        title="Design landing page",
        status="doing",
        importance="high",
    )
    task2 = workroom_repo.create_task(
        user_id=user_id,
        project_id=project1["id"],
        title="Write product copy",
        status="ready",
        importance="medium",
    )
    task3 = workroom_repo.create_task(
        user_id=user_id,
        project_id=project1["id"],
        title="Set up analytics",
        status="backlog",
        importance="low",
    )
    task4 = workroom_repo.create_task(
        user_id=user_id,
        project_id=project2["id"],
        title="Create email templates",
        status="doing",
        importance="high",
    )
    task5 = workroom_repo.create_task(
        user_id=user_id,
        project_id=project2["id"],
        title="Schedule social posts",
        status="blocked",
        importance="medium",
    )

    # Create threads/chats
    thread1 = workroom_repo.create_thread(
        user_id=user_id,
        task_id=task1["id"],
        title="Design discussion",
    )
    thread2 = workroom_repo.create_thread(
        user_id=user_id,
        task_id=task2["id"],
        title="Copy review",
    )

    # Add some seed messages
    workroom_repo.add_message(
        user_id=user_id,
        thread_id=thread1["id"],
        role="user",
        content="What do you think about the color scheme?",
    )
    workroom_repo.add_message(
        user_id=user_id,
        thread_id=thread1["id"],
        role="assistant",
        content="The color scheme looks good! I'd suggest making the CTA button more prominent. Should I draft some alternatives?",
    )

    return {
        "ok": True,
        "projects": 2,
        "tasks": 5,
        "threads": 2,
    }


class AssistantSuggestRequest(BaseModel):
    message: Optional[str] = Field(
        None,
        description="User message to the assistant (optional when thread_id provided)",
    )
    thread_id: Optional[str] = Field(
        None,
        description="Thread ID to aggregate pending user messages from",
    )
    trust_level: Optional[str] = Field(
        None,
        description="Override trust level (training_wheels, supervised, autonomous)",
    )


@router.post("/api/workroom/tasks/{task_id}/assistant-suggest")
async def assistant_suggest_for_task(
    task_id: str,
    body: AssistantSuggestRequest,
    request: Request,
    user_id: str = Depends(_get_user_id),
) -> Dict[str, Any]:
    """Get LLM-suggested operations for a task.

    Resolves tenant_id + user_id, calls propose_ops_for_user with focus_task_id,
    executes ops based on trust_mode, and returns operations, applied, pending.
    """
    from services import llm as llm_service
    from core.services.llm_executor import execute_ops
    from presentation.api.repos import user_settings
    import presentation.api.repos.workroom as workroom_module
    import logging

    logger = logging.getLogger(__name__)

    # Resolve tenant_id
    tenant_id, _ = workroom_module._resolve_identity(user_id)

    # Get trust mode from request body or settings
    if body.trust_level:
        trust_mode = body.trust_level
    else:
        settings = user_settings.get_settings(user_id)
        trust_mode = settings.get("trust_level", "training_wheels")
    # Map legacy "standard" to "supervised"
    if trust_mode == "standard":
        trust_mode = "supervised"

    # Verify task exists
    try:
        task = workroom_repo.get_task(user_id, task_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Task not found")

    # Get thread_id from task or request
    thread_id = body.thread_id
    if not thread_id and task.get("thread_id"):
        thread_id = task["thread_id"]

    # Aggregate pending user messages if thread_id provided
    input_messages = None
    if thread_id:
        # Acquire lock for this thread to prevent concurrent processing
        thread_lock = await _get_thread_lock(thread_id)
        async with thread_lock:
            # Get pending user messages since last assistant response
            pending_messages = workroom_repo.get_pending_user_messages(
                thread_id, user_id
            )
            if pending_messages:
                input_messages = [msg.get("content", "") for msg in pending_messages]

    # Fallback to single message if no thread_id or no pending messages
    if not input_messages:
        if not body.message:
            raise HTTPException(
                status_code=400, detail="Either message or thread_id must be provided"
            )
        input_messages = [body.message]

    # Propose operations with aggregated messages
    operations = llm_service.propose_ops_for_user(
        tenant_id=tenant_id,
        user_id=user_id,
        input_messages=input_messages,
        focus_task_id=task_id,
    )

    # Convert to typed operations for executor
    from core.domain.llm_ops import validate_operation

    typed_ops = []
    for op_dict in operations:
        try:
            op = validate_operation(op_dict)
            typed_ops.append(op)
        except ValueError as e:
            logger.warning(f"Invalid operation skipped: {e}")

    # Execute with trust gating
    result = execute_ops(
        typed_ops,
        tenant_id=tenant_id,
        user_id=user_id,
        trust_mode=trust_mode,
        thread_id=thread_id,
    )

    # Refresh task
    try:
        refreshed_task = workroom_repo.get_task(user_id, task_id)
    except ValueError:
        refreshed_task = task

    request_id = getattr(request.state, "request_id", None)

    # Write audit log
    audit_log.write_audit(
        "assistant_suggest",
        {
            "task_id": task_id,
            "user_id": user_id,
            "thread_id": thread_id,
            "message_count": len(input_messages),
            "operations_count": len(operations),
            "applied_count": len(result["applied"]),
            "pending_count": len(result["pending"]),
        },
        request_id=request_id,
    )

    return {
        "ok": True,
        "operations": operations,
        "applied": result["applied"],
        "pending": result["pending"],
        "errors": result["errors"],
        "task": refreshed_task,
    }


class ApproveOperationRequest(BaseModel):
    operation: Dict[str, Any] = Field(..., description="Operation to approve")


@router.post("/api/workroom/tasks/{task_id}/assistant-approve")
async def assistant_approve_operation_for_task(
    task_id: str,
    body: ApproveOperationRequest,
    request: Request,
    user_id: str = Depends(_get_user_id),
) -> Dict[str, Any]:
    """Approve and execute a pending operation for a task."""
    from core.services.llm_executor import execute_single_op_approved
    from core.domain.llm_ops import validate_operation
    import presentation.api.repos.workroom as workroom_module

    tenant_id, _ = workroom_module._resolve_identity(user_id)

    # Validate operation
    try:
        # Convert to dict if it's a Pydantic model
        operation_dict = body.operation
        if hasattr(operation_dict, "dict"):
            operation_dict = operation_dict.dict()
        elif hasattr(operation_dict, "model_dump"):
            operation_dict = operation_dict.model_dump()
        op = validate_operation(operation_dict)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid operation: {e}")

    # Get thread_id from task
    try:
        task = workroom_repo.get_task(user_id, task_id)
        thread_id = task.get("thread_id")
    except ValueError:
        thread_id = None

    # Execute approved operation (bypasses trust gating)
    result = execute_single_op_approved(
        op,
        tenant_id=tenant_id,
        user_id=user_id,
        thread_id=thread_id,
    )

    # Refresh task
    try:
        refreshed_task = workroom_repo.get_task(user_id, task_id)
    except ValueError:
        refreshed_task = None

    request_id = getattr(request.state, "request_id", None)
    audit_log.write_audit(
        "assistant_approve",
        {
            "task_id": task_id,
            "operation": body.operation,
            "result": result,
        },
        request_id=request_id,
    )

    return {
        "ok": result.get("ok", False),
        "result": result,
        "task": refreshed_task,
    }


class EditOperationRequest(BaseModel):
    operation: Dict[str, Any] = Field(..., description="Original operation")
    edited_params: Dict[str, Any] = Field(..., description="Edited parameters")


@router.post("/api/workroom/tasks/{task_id}/assistant-edit")
async def assistant_edit_operation_for_task(
    task_id: str,
    body: EditOperationRequest,
    request: Request,
    user_id: str = Depends(_get_user_id),
) -> Dict[str, Any]:
    """Edit and execute a pending operation for a task."""
    from core.services.llm_executor import execute_single_op_approved
    from core.domain.llm_ops import validate_operation
    import presentation.api.repos.workroom as workroom_module

    tenant_id, _ = workroom_module._resolve_identity(user_id)

    # Create edited operation (convert to dict if it's a Pydantic model)
    operation_dict = body.operation
    if hasattr(operation_dict, "dict"):
        operation_dict = operation_dict.dict()
    elif hasattr(operation_dict, "model_dump"):
        operation_dict = operation_dict.model_dump()

    edited_op_dict = {
        "op": operation_dict.get("op"),
        "params": {**operation_dict.get("params", {}), **body.edited_params},
    }

    # Validate edited operation
    try:
        op = validate_operation(edited_op_dict)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid edited operation: {e}")

    # Get thread_id from task
    try:
        task = workroom_repo.get_task(user_id, task_id)
        thread_id = task.get("thread_id")
    except ValueError:
        thread_id = None

    # Execute edited operation
    result = execute_single_op_approved(
        op,
        tenant_id=tenant_id,
        user_id=user_id,
        thread_id=thread_id,
    )

    # Refresh task
    try:
        refreshed_task = workroom_repo.get_task(user_id, task_id)
    except ValueError:
        refreshed_task = None

    request_id = getattr(request.state, "request_id", None)
    audit_log.write_audit(
        "assistant_edit",
        {
            "task_id": task_id,
            "original_operation": body.operation,
            "edited_operation": edited_op_dict,
            "result": result,
        },
        request_id=request_id,
    )

    return {
        "ok": result.get("ok", False),
        "result": result,
        "task": refreshed_task,
    }


class DeclineOperationRequest(BaseModel):
    operation: Dict[str, Any] = Field(..., description="Operation to decline")


@router.post("/api/workroom/tasks/{task_id}/assistant-decline")
async def assistant_decline_operation_for_task(
    task_id: str,
    body: DeclineOperationRequest,
    request: Request,
    user_id: str = Depends(_get_user_id),
) -> Dict[str, Any]:
    """Decline a pending operation for a task."""
    import presentation.api.repos.workroom as workroom_module

    tenant_id, _ = workroom_module._resolve_identity(user_id)

    # Just log the decline - no execution needed
    request_id = getattr(request.state, "request_id", None)
    audit_log.write_audit(
        "assistant_decline",
        {
            "task_id": task_id,
            "operation": body.operation,
        },
        request_id=request_id,
    )

    # Refresh task
    try:
        refreshed_task = workroom_repo.get_task(user_id, task_id)
    except ValueError:
        refreshed_task = None

    return {
        "ok": True,
        "task": refreshed_task,
    }


class UndoOperationRequest(BaseModel):
    operation: Dict[str, Any] = Field(..., description="Operation to undo")
    original_state: Optional[Dict[str, Any]] = Field(
        None, description="Original state before operation"
    )


@router.post("/api/workroom/tasks/{task_id}/assistant-undo")
async def assistant_undo_operation_for_task(
    task_id: str,
    body: UndoOperationRequest,
    request: Request,
    user_id: str = Depends(_get_user_id),
) -> Dict[str, Any]:
    """Undo a previously applied operation for a task."""
    from core.services.llm_executor import undo_operation
    from core.domain.llm_ops import validate_operation
    import presentation.api.repos.workroom as workroom_module

    tenant_id, _ = workroom_module._resolve_identity(user_id)

    # Validate operation
    try:
        # Convert to dict if it's a Pydantic model
        operation_dict = body.operation
        if hasattr(operation_dict, "dict"):
            operation_dict = operation_dict.dict()
        elif hasattr(operation_dict, "model_dump"):
            operation_dict = operation_dict.model_dump()
        op = validate_operation(operation_dict)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid operation: {e}")

    # Undo operation
    result = undo_operation(
        op,
        tenant_id=tenant_id,
        user_id=user_id,
        original_state=body.original_state,
    )

    # Refresh task
    try:
        refreshed_task = workroom_repo.get_task(user_id, task_id)
    except ValueError:
        refreshed_task = None

    request_id = getattr(request.state, "request_id", None)
    audit_log.write_audit(
        "assistant_undo",
        {
            "task_id": task_id,
            "operation": body.operation,
            "result": result,
        },
        request_id=request_id,
    )

    return {
        "ok": result.get("ok", False),
        "result": result,
        "task": refreshed_task,
    }

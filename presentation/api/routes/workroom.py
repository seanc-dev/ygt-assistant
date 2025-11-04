"""Workroom endpoints."""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Request, Depends, HTTPException
from pydantic import BaseModel, Field
from presentation.api.repos import workroom as workroom_repo, audit_log
from presentation.api.routes.queue import _get_user_id
import uuid

router = APIRouter()


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
) -> Dict[str, Any]:
    """Create a new thread.

    Creates a new thread under a task, or from an action if source_action_id is provided.
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
        },
        request_id=request_id,
    )

    return {
        "ok": True,
        "thread": thread,
    }


@router.patch("/api/workroom/task/{task_id}/status")
async def update_task_status(
    task_id: str,
    body: UpdateTaskStatusRequest,
    request: Request,
    user_id: str = Depends(_get_user_id),
) -> Dict[str, Any]:
    """Update task status.

    Valid statuses: todo, doing, done, blocked
    """
    valid_statuses = ["todo", "doing", "done", "blocked"]
    if body.status not in valid_statuses:
        raise HTTPException(
            status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}"
        )

    try:
        task = workroom_repo.update_task_status(user_id, task_id, body.status)
    except ValueError:
        raise HTTPException(status_code=404, detail="Task not found")

    # Audit log
    request_id = getattr(request.state, "request_id", None)
    audit_log.write_audit(
        "update_task_status",
        {
            "user_id": user_id,
            "task_id": task_id,
            "status": body.status,
        },
        request_id=request_id,
    )

    return {
        "ok": True,
        "task": task,
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

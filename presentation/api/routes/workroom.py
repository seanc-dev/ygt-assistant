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
    task_id: str = Field(..., description="Task ID to create thread under")
    title: str = Field(..., description="Thread title")
    prefs: Optional[Dict[str, Any]] = Field(default=None, description="Thread preferences")


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
    
    Creates a new thread under a task.
    """
    # Verify task exists
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
            "task_id": body.task_id,
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
            status_code=400,
            detail=f"Invalid status. Must be one of: {valid_statuses}"
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

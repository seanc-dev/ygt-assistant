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

router = APIRouter()

# Feature flag for seeding threads
FEATURE_SEED_THREADS = os.getenv("FEATURE_SEED_THREADS", "false").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
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
                "createdAt": p.get("created_at", datetime.now(timezone.utc).isoformat()),
                "updatedAt": p.get("updated_at", p.get("created_at", datetime.now(timezone.utc).isoformat())),
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
            "createdAt": project.get("created_at", datetime.now(timezone.utc).isoformat()),
            "updatedAt": project.get("updated_at", project.get("created_at", datetime.now(timezone.utc).isoformat())),
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
        transformed.append({
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
            "createdAt": task.get("created_at", datetime.now(timezone.utc).isoformat()),
            "updatedAt": task.get("updated_at", task.get("created_at", datetime.now(timezone.utc).isoformat())),
        })
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
            "updatedAt": task.get("updated_at", task.get("created_at", datetime.now(timezone.utc).isoformat())),
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
    task = workroom_repo.create_task(
        user_id=user_id,
        project_id=body["projectId"],
        title=body["title"],
        status=body.get("status", "backlog"),
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

    Valid statuses: backlog, ready, doing, blocked, done
    """
    valid_statuses = ["backlog", "ready", "doing", "blocked", "done", "todo"]
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

    # Dev-only: Automatically generate assistant response when user sends a message
    if DEV_MODE and body.role == "user":
        import asyncio

        # Generate a contextual response based on user message
        response_content = _generate_dev_response(body.content)

        # Add slight delay to simulate LLM processing (1-2 seconds)
        await asyncio.sleep(1.5)

        # Create assistant response
        assistant_message = workroom_repo.add_message(
            user_id=user_id,
            thread_id=thread_id,
            role="assistant",
            content=response_content,
        )

        # Return both messages
        return {
            "ok": True,
            "message": message,
            "assistant_message": assistant_message,
        }

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
        raise HTTPException(status_code=403, detail="Seed endpoint only available in dev mode")
    
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

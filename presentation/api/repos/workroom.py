"""Workroom stores (in-memory, interface for DB later)."""
from __future__ import annotations
from typing import Any, Dict, List
from datetime import datetime, timezone
import uuid

# In-memory stores: user_id -> data
_projects_store: Dict[str, List[Dict[str, Any]]] = {}
_tasks_store: Dict[str, List[Dict[str, Any]]] = {}
_threads_store: Dict[str, List[Dict[str, Any]]] = {}


def get_projects(user_id: str) -> List[Dict[str, Any]]:
    """Get all projects for a user."""
    return _projects_store.get(user_id, [])


def get_tasks(user_id: str, project_id: str = None) -> List[Dict[str, Any]]:
    """Get tasks for a user, optionally filtered by project."""
    all_tasks = _tasks_store.get(user_id, [])
    if project_id:
        return [t for t in all_tasks if t.get("project_id") == project_id]
    return all_tasks


def get_threads(user_id: str, task_id: str = None) -> List[Dict[str, Any]]:
    """Get threads for a user, optionally filtered by task."""
    all_threads = _threads_store.get(user_id, [])
    if task_id:
        return [t for t in all_threads if t.get("task_id") == task_id]
    return all_threads


def create_project(user_id: str, name: str, description: str = None, priority: str = "medium") -> Dict[str, Any]:
    """Create a new project."""
    project = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "name": name,
        "description": description,
        "priority": priority,
        "context": {
            "notes": None,
            "pinned_refs": [],
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    
    if user_id not in _projects_store:
        _projects_store[user_id] = []
    _projects_store[user_id].append(project)
    
    return project


def create_task(
    user_id: str,
    project_id: str,
    title: str,
    status: str = "todo",
    importance: str = "medium",
    due: str = None,
) -> Dict[str, Any]:
    """Create a new task."""
    task = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "project_id": project_id,
        "title": title,
        "status": status,
        "importance": importance,
        "due": due,
        "context": {
            "notes": None,
            "pinned_refs": [],
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    
    if user_id not in _tasks_store:
        _tasks_store[user_id] = []
    _tasks_store[user_id].append(task)
    
    return task


def create_thread(
    user_id: str,
    task_id: str,
    title: str,
    prefs: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """Create a new thread."""
    thread = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "task_id": task_id,
        "title": title,
        "messages": [],
        "context_refs": [],
        "prefs": prefs or {},
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    
    if user_id not in _threads_store:
        _threads_store[user_id] = []
    _threads_store[user_id].append(thread)
    
    return thread


def update_task_status(user_id: str, task_id: str, status: str) -> Dict[str, Any]:
    """Update task status."""
    tasks = _tasks_store.get(user_id, [])
    for task in tasks:
        if task["id"] == task_id:
            task["status"] = status
            task["updated_at"] = datetime.now(timezone.utc).isoformat()
            return task
    raise ValueError(f"Task {task_id} not found")


def get_task(user_id: str, task_id: str) -> Dict[str, Any]:
    """Get a single task by ID."""
    tasks = _tasks_store.get(user_id, [])
    for task in tasks:
        if task["id"] == task_id:
            return task
    raise ValueError(f"Task {task_id} not found")


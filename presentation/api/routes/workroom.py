"""Workroom endpoints."""
from __future__ import annotations
from typing import Any, Dict
from fastapi import APIRouter

router = APIRouter()


@router.get("/api/workroom/tree")
async def workroom_tree() -> Dict[str, Any]:
    """Get project/task/thread hierarchy.
    
    Returns tree structure: Project → Task → Threads.
    """
    return {"ok": True, "stub": True}


@router.post("/api/workroom/thread")
async def create_thread() -> Dict[str, Any]:
    """Create a new thread.
    
    Creates a new thread under a task.
    """
    return {"ok": True, "stub": True}


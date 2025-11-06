"""Notion sync endpoint stub."""
from __future__ import annotations
from typing import Any, Dict
from fastapi import APIRouter, Request, Depends, HTTPException
from pydantic import BaseModel
from presentation.api.routes.queue import _get_user_id
import os

router = APIRouter()

# Feature flag check
FEATURE_NOTION_SYNC = os.getenv("FEATURE_NOTION_SYNC", "false").lower() == "true"


class SyncWeeklyDigestRequest(BaseModel):
    """Request to sync weekly workload digest to Notion."""
    weekStart: str
    triaged: int
    completed: int
    utilizationPct: int


class SyncTasksProjectsRequest(BaseModel):
    """Request to sync tasks and projects to Notion."""
    tasks: list[Dict[str, Any]]
    projects: list[Dict[str, Any]]


@router.post("/api/notion/sync")
async def notion_sync(
    body: Dict[str, Any],
    request: Request,
    user_id: str = Depends(_get_user_id),
) -> Dict[str, Any]:
    """Sync workload data to Notion databases.
    
    This endpoint is a stub that reads commands from .cursor/commands/notiontodo.md.
    When FEATURE_NOTION_SYNC is enabled, it will execute Notion API calls.
    
    Body can contain:
    - weeklyDigest: WeeklyDigestRequest
    - tasksAndProjects: SyncTasksProjectsRequest
    """
    if not FEATURE_NOTION_SYNC:
        return {
            "ok": False,
            "error": "FEATURE_NOTION_SYNC is not enabled",
            "message": "Set FEATURE_NOTION_SYNC=true to enable Notion sync",
        }
    
    # TODO: Implement Notion sync logic
    # 1. Read .cursor/commands/notiontodo.md for command definitions
    # 2. Execute appropriate Notion API calls based on request type
    # 3. Update/create entries in Notion Tasks and Projects databases
    
    # For now, return a no-op response
    return {
        "ok": True,
        "message": "Notion sync stub - implementation pending",
        "user_id": user_id,
    }


"""Audit log endpoints."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Request, Depends, Query
from presentation.api.routes.queue import _get_user_id
from presentation.api.repos import audit_log

router = APIRouter()


@router.get("/api/audit/log")
async def get_audit_log(
    request: Request,
    limit: int = Query(default=100, ge=1, le=1000, description="Number of entries to return"),
    action_type: Optional[str] = Query(None, description="Filter by action type"),
    user_id: str = Depends(_get_user_id),
) -> Dict[str, Any]:
    """Get audit log entries.
    
    Query params:
    - limit: Number of entries to return (default: 100, max: 1000)
    - action_type: Optional filter by action type (e.g., "defer", "add_to_today")
    
    Returns audit log entries sorted by timestamp (newest first).
    """
    entries = audit_log.get_audit_log(limit=limit)
    
    # Filter by action type if provided
    if action_type:
        entries = [e for e in entries if e.get("action") == action_type]
    
    # Filter by user_id if details contain user_id
    user_entries = []
    for entry in entries:
        details = entry.get("details", {})
        if details.get("user_id") == user_id or not details.get("user_id"):
            user_entries.append(entry)
    
    return {
        "ok": True,
        "entries": user_entries,
        "total": len(user_entries),
        "limit": limit,
    }


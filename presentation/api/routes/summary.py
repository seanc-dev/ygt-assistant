"""Unified action items summary endpoint."""
from __future__ import annotations
from typing import Any, Dict, List
from fastapi import APIRouter, Request, Depends, Query
from presentation.api.routes.queue import _get_user_id
from presentation.api.services.unified_actions import generate_unified_action_items

router = APIRouter()


@router.get("/api/summary/queue")
async def summary_queue(
    request: Request,
    days: int = Query(default=7, ge=1, le=30, description="Number of days to look back"),
    user_id: str = Depends(_get_user_id),
) -> Dict[str, Any]:
    """Get unified action items summary (email, Teams, Docs changes).
    
    Returns summary of all action items across sources:
    - Email: threads needing response/approval
    - Teams: mentions and unread messages
    - Docs: recently modified documents
    
    Query params:
    - days: Number of days to look back (default: 7, max: 30)
    """
    action_items = await generate_unified_action_items(user_id, days=days)
    
    # Group by source for summary
    by_source = {
        "email": [a for a in action_items if a.get("source") == "email"],
        "teams": [a for a in action_items if a.get("source") == "teams"],
        "doc": [a for a in action_items if a.get("source") == "doc"],
    }
    
    # Group by category
    by_category = {
        "needs_response": [a for a in action_items if a.get("category") == "needs_response"],
        "needs_approval": [a for a in action_items if a.get("category") == "needs_approval"],
        "fyi": [a for a in action_items if a.get("category") == "fyi"],
    }
    
    # Group by priority
    by_priority = {
        "high": [a for a in action_items if a.get("priority") == "high"],
        "medium": [a for a in action_items if a.get("priority") == "medium"],
        "low": [a for a in action_items if a.get("priority") == "low"],
    }
    
    return {
        "ok": True,
        "total": len(action_items),
        "items": action_items,
        "summary": {
            "by_source": {
                "email": len(by_source["email"]),
                "teams": len(by_source["teams"]),
                "doc": len(by_source["doc"]),
            },
            "by_category": {
                "needs_response": len(by_category["needs_response"]),
                "needs_approval": len(by_category["needs_approval"]),
                "fyi": len(by_category["fyi"]),
            },
            "by_priority": {
                "high": len(by_priority["high"]),
                "medium": len(by_priority["medium"]),
                "low": len(by_priority["low"]),
            },
        },
    }


@router.get("/api/summary/recent")
async def summary_recent(
    request: Request,
    limit: int = Query(default=5, ge=1, le=20, description="Number of recent items to return"),
    user_id: str = Depends(_get_user_id),
) -> Dict[str, Any]:
    """Get recently accessed/created documents and threads.
    
    Returns recent items from various sources:
    - Email threads
    - Teams conversations
    - Documents (Word, Excel, PowerPoint)
    
    Query params:
    - limit: Maximum number of items to return (default: 5, max: 20)
    """
    # Get recent action items from unified actions (last 24 hours)
    action_items = await generate_unified_action_items(user_id, days=1)
    
    # Sort by timestamp (most recent first) and limit
    sorted_items = sorted(
        action_items,
        key=lambda x: x.get("timestamp") or x.get("created_at") or "",
        reverse=True
    )[:limit]
    
    # Format for frontend
    recent_items: List[Dict[str, Any]] = []
    for item in sorted_items:
        recent_items.append({
            "id": item.get("action_id") or item.get("thread_id") or item.get("id", ""),
            "title": item.get("preview", "")[:100] or item.get("subject", "Untitled"),
            "source": item.get("source", "unknown"),
            "preview": item.get("preview", "")[:200],
            "timestamp": item.get("timestamp") or item.get("created_at"),
            "thread_id": item.get("thread_id"),
        })
    
    return {
        "ok": True,
        "items": recent_items,
        "total": len(recent_items),
    }


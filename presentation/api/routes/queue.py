"""Queue (Action Items) endpoints."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import uuid
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, Field
from settings import DEFAULT_TZ
from presentation.api.repos import user_settings, audit_log
from presentation.api.utils.defer import compute_defer_until
from presentation.api.stores import proposed_blocks_store

router = APIRouter()


def _get_user_id(request: Request) -> str:
    """Get user ID from request (stub - will use auth in Phase 5)."""
    return request.cookies.get("user_id") or "default"

# In-memory queue store (will be replaced with DB in Phase 2+)
queue_store: Dict[str, Dict[str, Any]] = {}
defer_store: Dict[str, Dict[str, Any]] = {}  # action_id -> defer info


class ActionItem(BaseModel):
    """Action item model."""
    action_id: str = Field(..., description="UUID")
    source: str = Field(..., description="email|teams|doc")
    category: str = Field(..., description="needs_response|needs_approval|fyi")
    priority: str = Field(..., description="low|medium|high")
    preview: str
    thread_id: Optional[str] = None
    defer_until: Optional[str] = None  # ISO datetime
    defer_bucket: Optional[str] = None  # afternoon|tomorrow|this_week|next_week
    added_to_today: Optional[bool] = None


class DeferRequest(BaseModel):
    bucket: str = Field(..., description="afternoon|tomorrow|this_week|next_week")


class AddToTodayRequest(BaseModel):
    kind: str = Field(..., description="admin|work")
    tasks: Optional[List[str]] = None


@router.get("/api/queue")
async def get_queue(
    request: Request,
    limit: int = 5,
    offset: int = 0,
    user_id: str = Depends(_get_user_id),
    use_unified: bool = False,
) -> Dict[str, Any]:
    """Get queue of action items.
    
    Returns action items from Outlook, Teams, and Docs change summaries.
    Keeps ≤5 visible; preloads 10.
    
    Query params:
    - limit: Number of items to return (default: 5)
    - offset: Offset for pagination (default: 0)
    - use_unified: If true, fetch from unified sources (default: false, uses queue_store)
    """
    # If use_unified is true, fetch from unified sources
    if use_unified:
        try:
            from presentation.api.services.unified_actions import generate_unified_action_items
            unified_items = await generate_unified_action_items(user_id, days=7)
            
            # Merge with existing queue_store items
            for item in unified_items:
                if item["action_id"] not in queue_store:
                    queue_store[item["action_id"]] = {
                        **item,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }
        except Exception:
            pass  # Fallback to queue_store if unified fails
    
    # Filter out deferred items that haven't resurfaced yet
    try:
        tz = ZoneInfo(DEFAULT_TZ)
    except Exception:
        tz = timezone.utc
    now = datetime.now(tz)
    visible_items = []
    for item in queue_store.values():
        defer_info = defer_store.get(item["action_id"])
        if defer_info and defer_info.get("defer_until"):
            defer_until = datetime.fromisoformat(defer_info["defer_until"].replace("Z", "+00:00"))
            if defer_until > now:
                continue  # Skip items not yet resurfaced
        visible_items.append(item)
    
    # Sort by priority and creation time
    visible_items.sort(key=lambda x: (
        {"high": 0, "medium": 1, "low": 2}.get(x.get("priority", "medium"), 1),
        x.get("created_at", "")
    ))
    
    total = len(visible_items)
    items = visible_items[offset:offset + limit]
    
    return {
        "ok": True,
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.post("/api/queue/{action_id}/defer")
async def defer_action(
    action_id: str,
    body: DeferRequest,
    request: Request,
    user_id: str = Depends(_get_user_id),
) -> Dict[str, Any]:
    """Defer an action item.
    
    Computes defer_until based on bucket and user settings.
    Persists defer info and audits.
    """
    if action_id not in queue_store:
        raise HTTPException(status_code=404, detail="action_not_found")
    
    user_settings_data = user_settings.get_settings(user_id)
    try:
        tz = ZoneInfo(user_settings_data.get("time_zone", DEFAULT_TZ))
    except Exception:
        tz = timezone.utc
    now = datetime.now(tz)
    
    defer_until_iso, defer_bucket = compute_defer_until(
        body.bucket, now, user_settings_data
    )
    
    # If bucket is hidden, return error
    if defer_until_iso is None:
        raise HTTPException(
            status_code=400,
            detail=f"Defer bucket '{body.bucket}' is not available at this time"
        )
    
    request_id = getattr(request.state, "request_id", None)
    
    defer_store[action_id] = {
        "action_id": action_id,
        "defer_until": defer_until_iso,
        "defer_bucket": defer_bucket,
    }
    
    # Update queue item
    queue_store[action_id]["defer_until"] = defer_until_iso
    queue_store[action_id]["defer_bucket"] = defer_bucket
    
    # Write audit log
    audit_log.write_audit(
        "defer",
        {
            "action_id": action_id,
            "bucket": body.bucket,
            "defer_until": defer_until_iso,
            "user_id": user_id,
        },
        request_id=request_id,
    )
    
    return {
        "ok": True,
        "action_id": action_id,
        "defer_until": defer_until_iso,
        "defer_bucket": defer_bucket,
    }


@router.post("/api/queue/{action_id}/add-to-today")
async def add_to_today(
    action_id: str,
    body: AddToTodayRequest,
    request: Request,
    user_id: str = Depends(_get_user_id),
) -> Dict[str, Any]:
    """Add action item to today's schedule.
    
    Creates a ScheduleBlock stub.
    Persists and audits.
    """
    if action_id not in queue_store:
        raise HTTPException(status_code=404, detail="action_not_found")
    
    # Generate schedule block ID
    schedule_block_id = str(uuid.uuid4())
    
    # Create schedule block and add to proposed blocks store
    schedule_block = {
        "id": schedule_block_id,
        "user_id": user_id,
        "kind": body.kind,
        "tasks": body.tasks or [],
        "action_id": action_id,
        "estimated_minutes": 60,  # Default, will be estimated by LLM later
        "priority": queue_store[action_id].get("priority", "medium"),
        "estimated_start": None,  # Will be resolved by collision resolver
    }
    proposed_blocks_store.append(schedule_block)
    
    queue_store[action_id]["added_to_today"] = True
    
    request_id = getattr(request.state, "request_id", None)
    
    # Write audit log
    audit_log.write_audit(
        "add_to_today",
        {
            "action_id": action_id,
            "schedule_block_id": schedule_block_id,
            "kind": body.kind,
            "tasks": body.tasks or [],
            "user_id": user_id,
        },
        request_id=request_id,
    )
    
    return {
        "ok": True,
        "action_id": action_id,
        "schedule_block_id": schedule_block_id,
        "kind": body.kind,
    }


@router.post("/api/queue/{action_id}/reply")
async def reply_action(
    action_id: str,
    body: Dict[str, Any],
    request: Request,
    user_id: str = Depends(_get_user_id),
) -> Dict[str, Any]:
    """Reply to an action item (mock).
    
    Persists draft and audits.
    """
    if action_id not in queue_store:
        raise HTTPException(status_code=404, detail="action_not_found")
    
    draft_id = f"draft_{uuid.uuid4().hex[:8]}"
    
    request_id = getattr(request.state, "request_id", None)
    
    # Write audit log
    audit_log.write_audit(
        "reply",
        {
            "action_id": action_id,
            "draft_id": draft_id,
            "draft": body.get("draft", ""),
            "user_id": user_id,
        },
        request_id=request_id,
    )
    
    return {
        "ok": True,
        "action_id": action_id,
        "draft_id": draft_id,
    }

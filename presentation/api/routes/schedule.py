"""Schedule endpoints."""
from __future__ import annotations
from typing import Any, Dict, List
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Request, Depends
from presentation.api.repos import user_settings
from presentation.api.utils.schedule import generate_alternatives
from presentation.api.utils.collision import resolve_collisions
from presentation.api.routes.queue import _get_user_id
from presentation.api.deps.providers import get_calendar_provider_for
from presentation.api.stores import proposed_blocks_store
from settings import DEFAULT_TZ

router = APIRouter()


@router.get("/api/schedule/today")
async def schedule_today(
    request: Request,
    user_id: str = Depends(_get_user_id),
) -> Dict[str, Any]:
    """Get today's schedule merged with existing calendar events.
    
    Returns schedule blocks and existing events with collision resolution.
    """
    user_settings_data = user_settings.get_settings(user_id)
    work_hours = user_settings_data.get("work_hours", {"start": "09:00", "end": "17:00"})
    time_zone = user_settings_data.get("time_zone", DEFAULT_TZ)
    day_shape = user_settings_data.get("day_shape", {})
    buffer_minutes = day_shape.get("buffer_minutes", 5)
    
    try:
        tz = ZoneInfo(time_zone)
    except Exception:
        from datetime import timezone
        tz = timezone.utc
    
    now = datetime.now(tz)
    today_start = now.replace(
        hour=int(work_hours["start"].split(":")[0]),
        minute=int(work_hours["start"].split(":")[1]),
        second=0,
        microsecond=0
    )
    today_end = now.replace(
        hour=int(work_hours["end"].split(":")[0]),
        minute=int(work_hours["end"].split(":")[1]),
        second=0,
        microsecond=0
    )
    
    # Fetch existing events from calendar provider (mock or real)
    try:
        provider = get_calendar_provider_for("list_events", user_id)
        if hasattr(provider, "list_events_async"):
            existing_events_raw = await provider.list_events_async(
                today_start.isoformat(),
                today_end.isoformat()
            )
        else:
            existing_events_raw = provider.list_events(
                today_start.isoformat(),
                today_end.isoformat()
            )
        
        # Normalize event format
        existing_events = [
            {
                "id": e.get("id", ""),
                "title": e.get("title", e.get("subject", "Event")),
                "start": e.get("start", ""),
                "end": e.get("end", ""),
                "link": e.get("link", ""),
            }
            for e in existing_events_raw
        ]
    except Exception:
        # Fallback to empty if provider fails
        existing_events = []
    
    # Get proposed blocks from store
    proposed_blocks = [
        b for b in proposed_blocks_store
        if b.get("user_id") == user_id
    ]
    
    # Resolve collisions
    resolved_blocks = resolve_collisions(
        existing_events,
        proposed_blocks,
        buffer_minutes=buffer_minutes
    )
    
    return {
        "ok": True,
        "events": existing_events,
        "blocks": resolved_blocks,
        "date": now.date().isoformat(),
    }


@router.post("/api/schedule/alternatives")
async def schedule_alternatives(
    body: Dict[str, Any],
    request: Request,
    user_id: str = Depends(_get_user_id),
) -> Dict[str, Any]:
    """Generate 3 alternative schedule plans.
    
    Returns Focus-first, Meeting-friendly, and Balanced plans.
    Respects user_settings.day_shape and existing events.
    """
    user_settings_data = user_settings.get_settings(user_id)
    
    # Get existing events for today
    work_hours = user_settings_data.get("work_hours", {"start": "09:00", "end": "17:00"})
    time_zone = user_settings_data.get("time_zone", DEFAULT_TZ)
    
    try:
        tz = ZoneInfo(time_zone)
    except Exception:
        from datetime import timezone
        tz = timezone.utc
    
    now = datetime.now(tz)
    today_start = now.replace(
        hour=int(work_hours["start"].split(":")[0]),
        minute=int(work_hours["start"].split(":")[1]),
        second=0,
        microsecond=0
    )
    today_end = now.replace(
        hour=int(work_hours["end"].split(":")[0]),
        minute=int(work_hours["end"].split(":")[1]),
        second=0,
        microsecond=0
    )
    
    # Fetch existing events
    try:
        provider = get_calendar_provider_for("list_events", user_id)
        if hasattr(provider, "list_events_async"):
            existing_events_raw = await provider.list_events_async(
                today_start.isoformat(),
                today_end.isoformat()
            )
        else:
            existing_events_raw = provider.list_events(
                today_start.isoformat(),
                today_end.isoformat()
            )
        
        existing_events = [
            {
                "id": e.get("id", ""),
                "title": e.get("title", e.get("subject", "Event")),
                "start": e.get("start", ""),
                "end": e.get("end", ""),
            }
            for e in existing_events_raw
        ]
    except Exception:
        existing_events = body.get("existing_events", [])
    
    proposed_blocks = body.get("proposed_blocks", [])
    
    result = generate_alternatives(
        existing_events,
        proposed_blocks,
        user_settings_data,
    )
    
    return {"ok": True, **result}

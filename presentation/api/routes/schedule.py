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


@router.patch("/api/schedule/event/{event_id}")
async def update_event(
    event_id: str,
    body: Dict[str, Any],
    request: Request,
    user_id: str = Depends(_get_user_id),
) -> Dict[str, Any]:
    """Update an event's start and/or end time.
    
    Body should contain 'start' and/or 'end' as ISO datetime strings.
    Handles both calendar events (from provider) and proposed blocks (from store).
    """
    try:
        # Check if it's a proposed block first
        block = next(
            (b for b in proposed_blocks_store if b.get("id") == event_id and b.get("user_id") == user_id),
            None
        )
        
        if block:
            # Update block in store
            if "start" in body:
                block["start"] = body["start"]
            if "end" in body:
                block["end"] = body["end"]
            if "title" in body:
                block["title"] = body["title"]
            if "note" in body:
                block["note"] = body.get("note")
            return {"ok": True, "event": block}
        
        # Otherwise, it's a calendar event - update via provider
        provider = get_calendar_provider_for("create_events", user_id)
        
        # Prepare patch payload for Microsoft Graph format
        patch: Dict[str, Any] = {}
        if "start" in body:
            patch["start"] = {"dateTime": body["start"], "timeZone": "UTC"}
        if "end" in body:
            patch["end"] = {"dateTime": body["end"], "timeZone": "UTC"}
        if "title" in body:
            patch["subject"] = body["title"]
        # Note: Microsoft Graph doesn't have a direct "note" field for events
        # This would need to be stored separately or in event body
        
        # Use async method if available, otherwise sync
        if hasattr(provider, "update_event_async"):
            result = await provider.update_event_async(event_id, patch)
        else:
            result = provider.update_event(event_id, patch)
        
        return {"ok": True, "event": result}
    except Exception as e:
        # Return error response
        return {"ok": False, "error": str(e)}


@router.post("/api/schedule/interpret")
async def interpret_schedule_command(
    body: Dict[str, Any],
    request: Request,
    user_id: str = Depends(_get_user_id),
) -> Dict[str, Any]:
    """Interpret a natural language command for a schedule event.
    
    Body should contain 'eventId' and 'text'.
    Returns action type and parameters for the update.
    """
    event_id = body.get("eventId")
    text = body.get("text", "").strip().lower()
    
    if not event_id or not text:
        return {
            "ok": False,
            "action": "unknown",
            "confirmation": "Please provide a command.",
        }
    
    # Simple command interpretation (can be enhanced with LLM later)
    # Check for shift commands
    if any(word in text for word in ["move earlier", "shift earlier", "move back", "earlier"]):
        # Extract minutes if mentioned, default to 15
        minutes_match = None
        import re
        minutes_match = re.search(r"(\d+)\s*(?:min|minute|m)", text)
        minutes = -int(minutes_match.group(1)) if minutes_match else -15
        return {
            "ok": True,
            "action": "shift",
            "deltaMinutes": minutes,
            "confirmation": f"Moved {abs(minutes)} minutes earlier",
        }
    
    if any(word in text for word in ["move later", "shift later", "move forward", "later"]):
        minutes_match = None
        import re
        minutes_match = re.search(r"(\d+)\s*(?:min|minute|m)", text)
        minutes = int(minutes_match.group(1)) if minutes_match else 15
        return {
            "ok": True,
            "action": "shift",
            "deltaMinutes": minutes,
            "confirmation": f"Moved {minutes} minutes later",
        }
    
    # Resize commands
    if any(word in text for word in ["shorten", "make shorter", "reduce"]):
        minutes_match = None
        import re
        minutes_match = re.search(r"(\d+)\s*(?:min|minute|m)", text)
        minutes = -int(minutes_match.group(1)) if minutes_match else -15
        # This would need current event data to calculate new end time
        return {
            "ok": True,
            "action": "open_chat",
            "confirmation": "Please use 'Open full chat' for resize commands",
        }
    
    if any(word in text for word in ["extend", "make longer", "increase"]):
        minutes_match = None
        import re
        minutes_match = re.search(r"(\d+)\s*(?:min|minute|m)", text)
        minutes = int(minutes_match.group(1)) if minutes_match else 15
        return {
            "ok": True,
            "action": "open_chat",
            "confirmation": "Please use 'Open full chat' for resize commands",
        }
    
    # Defer commands
    if any(word in text for word in ["defer", "postpone", "move to afternoon"]):
        return {
            "ok": True,
            "action": "defer",
            "period": "afternoon",
            "confirmation": "Deferred to afternoon",
        }
    
    if any(word in text for word in ["move to tomorrow", "tomorrow"]):
        return {
            "ok": True,
            "action": "defer",
            "period": "tomorrow_morning",
            "confirmation": "Deferred to tomorrow morning",
        }
    
    # Rename commands
    if text.startswith("rename") or text.startswith("call it"):
        new_title = text.replace("rename", "").replace("call it", "").strip()
        if new_title:
            return {
                "ok": True,
                "action": "rename",
                "title": new_title,
                "confirmation": f"Renamed to '{new_title}'",
            }
    
    # Note commands
    if text.startswith("note") or text.startswith("add note"):
        note_text = text.replace("note", "").replace("add note", "").strip()
        if note_text:
            return {
                "ok": True,
                "action": "note",
                "note": note_text,
                "confirmation": "Note added",
            }
    
    # Open chat fallback
    if any(word in text for word in ["chat", "help", "open", "full"]):
        return {
            "ok": True,
            "action": "open_chat",
            "confirmation": "Opening full chat",
        }
    
    # Unknown command
    return {
        "ok": False,
        "action": "unknown",
        "confirmation": "I didn't understand that. Try 'Open full chat' for help.",
    }

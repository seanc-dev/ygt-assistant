"""Schedule endpoints."""
from __future__ import annotations
from typing import Any, Dict, List
from fastapi import APIRouter, Request, Depends
from presentation.api.repos import user_settings
from presentation.api.utils.schedule import generate_alternatives
from presentation.api.routes.queue import _get_user_id

router = APIRouter()

# Mock existing events store
existing_events_store: List[Dict[str, Any]] = []


@router.get("/api/schedule/today")
async def schedule_today(
    request: Request,
    user_id: str = Depends(_get_user_id),
) -> Dict[str, Any]:
    """Get today's schedule merged with existing calendar events.
    
    Returns schedule blocks and existing events.
    """
    # TODO: Merge with real calendar events (mock for now)
    return {
        "ok": True,
        "events": existing_events_store,
        "blocks": [],
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
    existing_events = body.get("existing_events", existing_events_store)
    proposed_blocks = body.get("proposed_blocks", [])
    
    result = generate_alternatives(
        existing_events,
        proposed_blocks,
        user_settings_data,
    )
    
    return {"ok": True, **result}

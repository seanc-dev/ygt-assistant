from __future__ import annotations
from typing import Any, Dict, List
from fastapi import APIRouter

from settings import FEATURE_GRAPH_LIVE, FEATURE_LIVE_CREATE_EVENTS
from services.providers.registry import get_calendar_provider
from utils.metrics import increment


router = APIRouter()


def _live_enabled(flag: bool) -> bool:
    return bool(FEATURE_GRAPH_LIVE and flag)


@router.post("/actions/live/create-events")
async def create_events_live(user_id: str = "default", body: Dict[str, Any] | None = None) -> Dict[str, Any]:
    if not _live_enabled(FEATURE_LIVE_CREATE_EVENTS):
        return {"ok": False, "live": False}
    p = get_calendar_provider(user_id)
    events = (body or {}).get("events") or []
    if hasattr(p, "create_events_batch"):
        out = p.create_events_batch(events)
    else:
        out = [p.create_event(e) for e in events]
    increment("live.events.created", n=len(out))
    return {"ok": True, "events": out}



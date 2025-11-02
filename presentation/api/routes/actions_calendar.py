from __future__ import annotations
from typing import Any, Dict, List
from fastapi import APIRouter, Request

from settings import FEATURE_GRAPH_LIVE, FEATURE_LIVE_CREATE_EVENTS
from presentation.api.deps.providers import get_calendar_provider_for
from utils.metrics import increment
from presentation.api.state import created_events_store, history_log


router = APIRouter()


def _live_enabled(flag: bool) -> bool:
    return bool(FEATURE_GRAPH_LIVE and flag)


@router.post("/actions/live/create-events")
async def create_events_live(
    request: Request, user_id: str = "default", body: Dict[str, Any] | None = None
) -> Dict[str, Any]:
    if not _live_enabled(FEATURE_LIVE_CREATE_EVENTS):
        return {"ok": False, "live": False}
    uid = request.cookies.get("ygt_user") or user_id or "default"
    p = get_calendar_provider_for("create_events", uid)
    events = (body or {}).get("events") or []
    if hasattr(p, "create_event_async"):
        out = [
            await p.create_event_async(e) for e in events  # type: ignore[attr-defined]
        ]
    elif hasattr(p, "create_events_batch"):
        out = p.create_events_batch(events)
    else:
        out = [p.create_event(e) for e in events]
    for ev in out:
        if ev.get("id"):
            created_events_store[ev["id"]] = ev
    if out:
        history_log.append(
            {
                "ts": "now",
                "verb": "create",
                "object": "event",
                "ids": [e.get("id") for e in out],
                "links": [e.get("webLink") for e in out],
            }
        )
    increment("live.events.created", n=len(out))
    return {"ok": True, "events": out}


@router.post("/actions/live/undo-event/{event_id}")
async def undo_event_live(
    request: Request, user_id: str, event_id: str
) -> Dict[str, Any]:
    if not _live_enabled(FEATURE_LIVE_CREATE_EVENTS):
        return {"ok": False, "live": False}
    ev = created_events_store.get(event_id)
    if not ev:
        return {"ok": False, "error": "not_found"}
    uid = request.cookies.get("ygt_user") or user_id or "default"
    p = get_calendar_provider_for("create_events", uid)
    try:
        # Best-effort delete via provider
        if hasattr(p, "delete_event_async"):
            await p.delete_event_async(event_id)  # type: ignore[attr-defined]
        elif hasattr(p, "delete_event"):
            p.delete_event(event_id)
        # Only remove from local store after successful delete
        created_events_store.pop(event_id, None)
        history_log.append(
            {"ts": "now", "verb": "undo", "object": "event", "id": event_id}
        )
        increment("undo.success")
        return {"ok": True, "deleted": True}
    except Exception:
        increment("live.action.error")
        # Keep the event in the store so user can retry undo later
        return {"ok": False, "deleted": False, "retry": True}

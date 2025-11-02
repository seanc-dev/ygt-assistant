"""Status and flags endpoint."""
from __future__ import annotations
from typing import Any, Dict
from fastapi import APIRouter
from settings import (
    FEATURE_GRAPH_LIVE,
    FEATURE_LIVE_LIST_INBOX,
    FEATURE_LIVE_SEND_MAIL,
    FEATURE_LIVE_CREATE_EVENTS,
    FEATURE_ALTERNATIVES,
    FEATURE_TRANSLATION,
    FEATURE_WEATHER_NEWS,
    PROVIDER,
    USE_MOCK_GRAPH,
)

router = APIRouter()


@router.get("/api/status/flags")
async def status_flags() -> Dict[str, Any]:
    """Get feature flags status.
    
    Returns all feature flags as booleans for frontend use.
    """
    return {
        "ok": True,
        "flags": {
            "FEATURE_GRAPH_LIVE": bool(FEATURE_GRAPH_LIVE),
            "FEATURE_LIVE_LIST_INBOX": bool(FEATURE_LIVE_LIST_INBOX),
            "FEATURE_LIVE_SEND_MAIL": bool(FEATURE_LIVE_SEND_MAIL),
            "FEATURE_LIVE_CREATE_EVENTS": bool(FEATURE_LIVE_CREATE_EVENTS),
            "FEATURE_ALTERNATIVES": bool(FEATURE_ALTERNATIVES),
            "FEATURE_TRANSLATION": bool(FEATURE_TRANSLATION),
            "FEATURE_WEATHER_NEWS": bool(FEATURE_WEATHER_NEWS),
            "PROVIDER": PROVIDER,
            "USE_MOCK_GRAPH": bool(USE_MOCK_GRAPH),
        },
    }


"""Settings endpoints."""
from __future__ import annotations
from typing import Any, Dict
from fastapi import APIRouter, Request, Depends
from pydantic import BaseModel
from presentation.api.repos import user_settings

router = APIRouter()


def _get_user_id(request: Request) -> str:
    """Get user ID from request (stub - will use auth in Phase 5)."""
    # TODO: Extract from auth token
    return request.cookies.get("user_id") or "default"


@router.get("/api/settings")
async def get_settings(
    request: Request,
    user_id: str = Depends(_get_user_id),
) -> Dict[str, Any]:
    """Get user settings.
    
    Returns work hours, translation rules, trust level, UI preferences.
    """
    settings = user_settings.get_settings(user_id)
    return {"ok": True, **settings}


@router.put("/api/settings")
async def update_settings(
    body: Dict[str, Any],
    request: Request,
    user_id: str = Depends(_get_user_id),
) -> Dict[str, Any]:
    """Update user settings.
    
    Updates work hours, translation rules, trust level, UI preferences.
    Validates time strings (HH:MM) and IANA timezone.
    """
    try:
        updated = user_settings.update_settings(user_id, body)
        return {"ok": True, **updated}
    except ValueError as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=str(e))

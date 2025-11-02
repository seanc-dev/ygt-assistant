"""Brief endpoint."""
from __future__ import annotations
from typing import Any, Dict
from fastapi import APIRouter

router = APIRouter()


@router.get("/api/brief/today")
async def brief_today() -> Dict[str, Any]:
    """Get today's brief with optional weather/news.
    
    Returns summary and optional weather/news if enabled.
    """
    return {"ok": True, "stub": True}


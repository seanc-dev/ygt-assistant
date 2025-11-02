"""Unified action items summary endpoint."""
from __future__ import annotations
from typing import Any, Dict
from fastapi import APIRouter

router = APIRouter()


@router.get("/summary/queue")
async def summary_queue() -> Dict[str, Any]:
    """Get unified action items summary (email, Teams, Docs changes).
    
    Returns summary of all action items across sources.
    """
    return {"ok": True, "stub": True}


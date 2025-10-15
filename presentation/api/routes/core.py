from __future__ import annotations
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Query
from core.store import get_store
from core.writer import write_semantic

router = APIRouter()

@router.get("/core/context")
async def core_context(for_: Optional[str] = Query(default=None, alias="for")) -> Dict[str, Any]:
    store = get_store()
    return {
        "episodic": [m.__dict__ for m in store.list_by_level("episodic")][:5],
        "semantic": [m.__dict__ for m in store.list_by_level("semantic")][:5],
        "procedural": [m.__dict__ for m in store.list_by_level("procedural")][:5],
        "narrative": [m.__dict__ for m in store.list_by_level("narrative")][:5],
    }

@router.post("/core/notes")
async def core_notes(body: Dict[str, Any]) -> Dict[str, Any]:
    item = write_semantic(str(body.get("fact") or ""), source=body.get("source"))
    return {"ok": True, "id": item.id}

@router.get("/core/preview")
async def core_preview(intent: Optional[str] = None) -> Dict[str, Any]:
    store = get_store()
    return {
        "semantic": [m.__dict__ for m in store.list_by_level("semantic")][:5],
        "narrative": [m.__dict__ for m in store.list_by_level("narrative")][:5],
    }

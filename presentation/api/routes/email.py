from __future__ import annotations
from typing import Any, Dict, List
from fastapi import APIRouter
import os
from services.gmail import GmailService
from services.microsoft_email import MicrosoftEmailProvider
from presentation.api.state import drafts_store, history_log

router = APIRouter()

def _is_true(v: str | None) -> bool:
    return (v or "").strip().lower() in {"1", "true", "yes", "on"}


@router.post("/email/drafts")
async def email_create_draft(body: Dict[str, Any]) -> Dict[str, Any]:
    # During llm-loop, TestClient runs an event loop; avoid anyio.run in email provider by using mock path
    if _is_true(os.getenv("USE_MOCK_GRAPH")):
        g = GmailService()
        d = g.create_draft(body.get("to") or [], body.get("subject") or "", body.get("body") or "")
        drafts_store[d["id"]] = d
        return d
    # Otherwise, if live Microsoft is desired, use provider directly (sync wrapper internally)
    p = MicrosoftEmailProvider("default")
    d = p.create_draft(body.get("to") or [], body.get("subject") or "", body.get("body") or "")
    drafts_store[d["id"]] = d
    return d

@router.post("/email/send/{draft_id}")
async def email_send(draft_id: str) -> Dict[str, Any]:
    g = GmailService()
    out = g.send(draft_id)
    if draft_id in drafts_store:
        drafts_store[draft_id]["status"] = "sent"
    history_log.append({"ts": "now", "verb": "send", "object": "draft", "id": draft_id})
    return out

@router.get("/drafts")
async def list_drafts() -> List[Dict[str, Any]]:
    return list(drafts_store.values())

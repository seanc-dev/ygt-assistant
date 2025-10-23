from __future__ import annotations
from typing import Any, Dict, List
from fastapi import APIRouter
import os

from settings import (
    FEATURE_GRAPH_LIVE,
    FEATURE_LIVE_LIST_INBOX,
    FEATURE_LIVE_SEND_MAIL,
)
from services.providers.registry import get_email_provider
from utils.metrics import increment


router = APIRouter()


def _is_true(v: str | None) -> bool:
    return (v or "").strip().lower() in {"1", "true", "yes", "on"}


def _live_enabled(action_flag: bool) -> bool:
    return bool(FEATURE_GRAPH_LIVE and action_flag)


@router.get("/actions/live/inbox")
async def list_inbox_live(user_id: str = "default", limit: int = 5) -> Dict[str, Any]:
    if not _live_enabled(FEATURE_LIVE_LIST_INBOX):
        return {"ok": False, "live": False}
    p = get_email_provider(user_id)
    if not hasattr(p, "list_inbox"):
        return {"ok": False, "error": "not_supported"}
    items = p.list_inbox(limit)
    increment("live.inbox.listed", n=len(items))
    return {"ok": True, "items": items}


@router.post("/actions/live/send")
async def send_mail_live(user_id: str = "default", body: Dict[str, Any] | None = None) -> Dict[str, Any]:
    if not _live_enabled(FEATURE_LIVE_SEND_MAIL):
        return {"ok": False, "live": False}
    b = body or {}
    to = b.get("to") or ["user@example.com"]
    subj = b.get("subject") or "[YGT] Test"
    txt = b.get("body") or "Hello from YGT"
    p = get_email_provider(user_id)
    out = p.send_message(to, subj, txt)
    increment("live.mail.sent")
    return {"ok": True, **out}



from __future__ import annotations
from typing import Any, Dict
from fastapi import APIRouter, HTTPException, Query, Request, Response
from services.whatsapp import parse_webhook as _wa_parse, send_buttons as _wa_send_buttons, send_text as _wa_send_text
from .helpers import actions_approve, actions_edit, actions_skip, email_send

router = APIRouter()

@router.get("/whatsapp/webhook")
async def whatsapp_verify(mode: str = Query(""), token: str = Query(""), challenge: str = Query("")):
    from os import getenv
    verify_token = getenv("WHATSAPP_VERIFY_TOKEN", "")
    if mode == "subscribe" and token and verify_token and token == verify_token:
        return Response(content=challenge, media_type="text/plain")
    raise HTTPException(status_code=403, detail="forbidden")

@router.post("/whatsapp/webhook")
async def whatsapp_webhook(req: Request) -> Dict[str, Any]:
    try:
        body = await req.json()
    except Exception:
        body = {}
    parsed = _wa_parse(body)
    try:
        if parsed.get("type") == "button":
            bid = parsed.get("button_id") or ""
            if bid.startswith("approve:"):
                aid = bid.split(":", 1)[1]
                return await actions_approve(aid)
            if bid.startswith("edit:"):
                aid = bid.split(":", 1)[1]
                return await actions_edit(aid, {"instructions": "tweak"})
            if bid.startswith("skip:"):
                aid = bid.split(":", 1)[1]
                return await actions_skip(aid)
            if bid.startswith("send:"):
                did = bid.split(":", 1)[1]
                return await email_send(did)
        if parsed.get("type") == "text":
            text = (parsed.get("text") or "").strip().lower()
            if text.startswith("approve "):
                aid = text.split(" ", 1)[1]
                return await actions_approve(aid)
            if text.startswith("skip "):
                aid = text.split(" ", 1)[1]
                return await actions_skip(aid)
            if text.startswith("send "):
                did = text.split(" ", 1)[1]
                return await email_send(did)
    except Exception:
        pass
    return {"ok": True, "parsed": parsed}

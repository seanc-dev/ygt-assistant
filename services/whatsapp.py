from __future__ import annotations
from typing import Any, Dict, List, Optional
import httpx
import os

WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")


def _headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }


def send_text(to: str, text: str) -> Dict[str, Any]:
    url = f"https://graph.facebook.com/v17.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    payload = {"messaging_product": "whatsapp", "to": to, "text": {"body": text}}
    with httpx.Client(timeout=10) as c:
        r = c.post(url, json=payload, headers=_headers())
        r.raise_for_status()
        return r.json()


def send_buttons(to: str, text: str, buttons: List[Dict[str, str]]) -> Dict[str, Any]:
    url = f"https://graph.facebook.com/v17.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    # WhatsApp interactive buttons sample structure
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": text},
            "action": {"buttons": [{"type": "reply", "reply": {"id": b.get("id"), "title": b.get("label")}} for b in buttons]},
        },
    }
    with httpx.Client(timeout=10) as c:
        r = c.post(url, json=payload, headers=_headers())
        r.raise_for_status()
        return r.json()


def send_list(to: str, header: str, rows: List[Dict[str, str]]) -> Dict[str, Any]:
    url = f"https://graph.facebook.com/v17.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "body": {"text": header},
            "action": {
                "button": "Select",
                "sections": [{"title": "Options", "rows": rows}],
            },
        },
    }
    with httpx.Client(timeout=10) as c:
        r = c.post(url, json=payload, headers=_headers())
        r.raise_for_status()
        return r.json()


def parse_webhook(payload: Dict[str, Any]) -> Dict[str, Any]:
    # Simplified parser for WhatsApp Cloud API webhooks
    entry = (payload.get("entry") or [{}])[0]
    changes = (entry.get("changes") or [{}])[0]
    value = changes.get("value") or {}
    messages = value.get("messages") or []
    contacts = value.get("contacts") or []
    if not messages:
        return {"type": "unknown"}
    msg = messages[0]
    user_id = (contacts[0].get("wa_id") if contacts else None) or value.get("metadata", {}).get("phone_number_id")
    if msg.get("type") == "text":
        return {"type": "text", "text": msg.get("text", {}).get("body", ""), "user_id": user_id}
    if msg.get("type") == "interactive":
        interactive = msg.get("interactive", {})
        if "button_reply" in interactive:
            br = interactive["button_reply"]
            return {"type": "button", "button_id": br.get("id"), "title": br.get("title"), "user_id": user_id}
        if "list_reply" in interactive:
            lr = interactive["list_reply"]
            return {"type": "list", "id": lr.get("id"), "title": lr.get("title"), "user_id": user_id}
    return {"type": "unknown", "user_id": user_id}

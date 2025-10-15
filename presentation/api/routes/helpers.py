from __future__ import annotations
from typing import Any, Dict
from presentation.api.state import approvals_store
from presentation.api.state import drafts_store  # noqa: F401 (referenced by email routes)
from presentation.api.state import history_log

async def actions_approve(approval_id: str) -> Dict[str, Any]:
    a = approvals_store.get(approval_id)
    if not a:
        return {"error": "not_found"}
    a["status"] = "approved"
    history_log.append({"ts": "now", "verb": "approve", "object": "approval", "id": approval_id})
    return a

async def actions_edit(approval_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
    a = approvals_store.get(approval_id)
    if not a:
        return {"error": "not_found"}
    a["status"] = "edited"
    a["edit_instructions"] = body.get("instructions")
    history_log.append({"ts": "now", "verb": "edit", "object": "approval", "id": approval_id, "instructions": body.get("instructions")})
    return a

async def actions_skip(approval_id: str) -> Dict[str, Any]:
    a = approvals_store.get(approval_id)
    if not a:
        return {"error": "not_found"}
    a["status"] = "skipped"
    history_log.append({"ts": "now", "verb": "skip", "object": "approval", "id": approval_id})
    return a

async def email_send(draft_id: str) -> Dict[str, Any]:
    # This proxy is used by whatsapp routes
    from services.gmail import GmailService
    g = GmailService()
    out = g.send(draft_id)
    # history is appended in email routes as well; duplicate is harmless in POC
    history_log.append({"ts": "now", "verb": "send", "object": "draft", "id": draft_id})
    return out



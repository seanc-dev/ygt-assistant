from __future__ import annotations
from typing import Any, Dict, List

from fastapi import APIRouter

from presentation.api.routes.actions import (
    actions_scan as _actions_scan,
    actions_approve as _actions_approve,
    actions_skip as _actions_skip,
)


router = APIRouter()


@router.post("/chat")
async def chat(body: Dict[str, Any]) -> Dict[str, Any]:
    """Minimal chat endpoint to stand in for WhatsApp.

    Commands:
    - "scan" → propose approvals
    - "approve <id>" → approve given approval id
    - "skip <id>" → skip given approval id
    """

    try:
        text = str(body.get("text") or "").strip()
        if not text:
            return {
                "messages": [
                    {
                        "role": "assistant",
                        "content": "Say 'scan' to propose actions.",
                    }
                ]
            }

        lowered = text.lower()
        if lowered == "scan" or lowered.startswith("scan "):
            approvals = await _actions_scan({"domains": ["email", "calendar"]})
            preview = [
                {
                    "id": a.get("id"),
                    "title": a.get("title") or a.get("summary"),
                    "kind": a.get("kind"),
                    "status": a.get("status"),
                }
                for a in approvals
            ]
            return {
                "messages": [
                    {
                        "role": "assistant",
                        "content": f"Proposed {len(approvals)} approval(s). Reply 'approve <id>' or 'skip <id>'.",
                    }
                ],
                "approvals": preview,
            }

        if lowered.startswith("approve "):
            _, _, aid = lowered.partition(" ")
            res = await _actions_approve(aid)
            if res.get("error"):
                return {
                    "messages": [{"role": "assistant", "content": "Not found."}]
                }
            return {
                "messages": [
                    {
                        "role": "assistant",
                        "content": f"Approved {aid}. Type 'undo {aid}' in the UI if needed.",
                    }
                ]
            }

        if lowered.startswith("skip "):
            _, _, aid = lowered.partition(" ")
            res = await _actions_skip(aid)
            if res.get("error"):
                return {
                    "messages": [{"role": "assistant", "content": "Not found."}]
                }
            return {"messages": [{"role": "assistant", "content": f"Skipped {aid}."}]}

        return {
            "messages": [
                {
                    "role": "assistant",
                    "content": "Unknown command. Try: 'scan', 'approve <id>', or 'skip <id>'.",
                }
            ]
        }
    except Exception as e:
        # Return a friendly error rather than a 500 to avoid hangs in the UI
        return {
            "messages": [
                {
                    "role": "assistant",
                    "content": f"Sorry, something went wrong: {type(e).__name__}",
                }
            ]
        }

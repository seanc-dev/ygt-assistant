from __future__ import annotations
from typing import Any, Dict, List


def summarise_and_propose(context: Dict[str, Any], core_ctx: Dict[str, Any]) -> List[Dict[str, Any]]:
    # If live inbox items are provided in context, propose actions from them
    inbox = context.get("inbox") or []
    if isinstance(inbox, list) and inbox:
        approvals: List[Dict[str, Any]] = []
        for it in inbox[:10]:
            subj = (it or {}).get("subject") or "Email"
            sender = (it or {}).get("from") or ""
            preview = (it or {}).get("preview") or ""
            link = (it or {}).get("link") or ""
            msg_id = (it or {}).get("id") or ""
            approvals.append(
                {
                    "id": f"inbox-{msg_id}" if msg_id else f"inbox-{abs(hash(subj+sender))}",
                    "kind": "email",
                    "source": "inbox",
                    "title": subj or (f"Email from {sender}" if sender else "Email"),
                    "summary": preview,
                    "metadata": {"sender": sender, "message_id": msg_id, "link": link},
                    "status": "proposed",
                }
            )
        return approvals
    # Fallback POC suggestion when no inbox context available
    return [
        {
            "id": "appr-1",
            "kind": "email",
            "source": "llm",
            "title": "Follow up on top email",
            "summary": "Suggest replying to the most urgent email.",
            "payload": context,
            "risk": "low",
            "status": "proposed",
        }
    ]


def draft_email(intent: Dict[str, Any], tone: str | None, core_ctx: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": "draft-1",
        "to": intent.get("to") or [],
        "subject": intent.get("subject") or "Quick, calm update",
        "body": f"Hey, just following up. Tone: {tone or 'calm'}",
        "tone": tone or "neutral",
        "status": "proposed",
        "risk": "low",
    }

from __future__ import annotations
from typing import Any, Dict, List


def summarise_and_propose(context: Dict[str, Any], core_ctx: Dict[str, Any]) -> List[Dict[str, Any]]:
    # POC: return a single low-risk approval suggestion
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

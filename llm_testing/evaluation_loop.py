"""Minimal evaluation loop adapted to current FastAPI via backend adapters."""

from __future__ import annotations
from typing import List, Dict, Any


class MinimalEvaluationLoop:
    """Drive simple end-to-end checks through the backend adapter."""

    def __init__(self, backend: Any) -> None:
        self.backend = backend

    def run_smoke(self) -> Dict[str, Any]:
        # 1) Scan for actions
        approvals = self.backend.actions_scan(["email", "calendar"]) or []
        # 2) If any approval, approve first
        approved = None
        if approvals:
            approved = self.backend.actions_approve(approvals[0].get("id", ""))
        # 3) Create and send a draft
        draft = self.backend.email_create_draft(
            ["test@example.com"], "Hello", "Hi there"
        )
        sent = self.backend.email_send(draft.get("id", ""))
        # 4) Plan today
        plan = self.backend.calendar_plan_today()
        # 5) Optional WhatsApp webhook (skip if route disabled)
        try:
            wa = self.backend.whatsapp_post(
                {
                    "entry": [
                        {
                            "changes": [
                                {
                                    "value": {
                                        "messages": [
                                            {
                                                "type": "text",
                                                "text": {"body": "approve 123"},
                                            }
                                        ],
                                        "contacts": [{"wa_id": "tester"}],
                                    }
                                }
                            ]
                        }
                    ]
                }
            )
        except Exception:
            wa = None
        return {
            "approvals": approvals,
            "approved": approved,
            "draft": draft,
            "sent": sent,
            "plan": plan,
            "wa": wa,
        }

from __future__ import annotations
from typing import Any, Dict, List


class GmailService:
    def list_unread(self) -> List[Dict[str, Any]]:
        return []

    def create_draft(self, to: List[str], subject: str, body: str) -> Dict[str, Any]:
        return {"id": "local-draft", "to": to, "subject": subject, "body": body}

    def send(self, draft_id: str) -> Dict[str, Any]:
        return {"id": draft_id, "status": "sent"}

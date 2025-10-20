from __future__ import annotations
from typing import Any, Dict, List

from services.providers.registry import get_email_provider


class GmailService:
    """Shim that delegates to the configured email provider.

    NOTE: Kept name for backward compatibility with existing imports.
    """

    def __init__(self, user_id: str | None = None) -> None:
        self._user_id = user_id or "default"

    def list_unread(self) -> List[Dict[str, Any]]:
        prov = get_email_provider(self._user_id)
        # Minimal filter to emulate unread inbox in stub context
        return prov.list_threads(q="label:inbox -label:read", max_n=10)

    def create_draft(self, to: List[str], subject: str, body: str) -> Dict[str, Any]:
        prov = get_email_provider(self._user_id)
        return prov.create_draft(to, subject, body)

    def send(self, draft_id: str) -> Dict[str, Any]:
        prov = get_email_provider(self._user_id)
        return prov.send_draft(draft_id)

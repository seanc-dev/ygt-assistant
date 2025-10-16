from __future__ import annotations
from typing import Any, Dict, List


class EmailProvider:
    """Abstract email provider interface.

    Implementations must avoid logging message bodies or tokens.
    """

    def list_threads(self, q: str, max_n: int) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def create_draft(self, to: List[str], subject: str, body: str) -> Dict[str, Any]:
        raise NotImplementedError

    def send_draft(self, draft_id: str) -> Dict[str, Any]:
        raise NotImplementedError

    def send_message(self, to: List[str], subject: str, body: str) -> Dict[str, Any]:
        raise NotImplementedError

    def get_message(self, message_id: str) -> Dict[str, Any]:
        raise NotImplementedError

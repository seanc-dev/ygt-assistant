from typing import Dict, Any
from infra.repos.interfaces import ClientSessionsRepo


class MemoryClientSessionsRepo(ClientSessionsRepo):
    def __init__(self) -> None:
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def create(self, user_id: str, token: str, expires_at: str | None = None) -> None:
        self._sessions[token] = {
            "user_id": user_id,
            "expires_at": expires_at,
        }

    def get(self, token: str) -> Dict[str, Any] | None:
        return self._sessions.get(token)

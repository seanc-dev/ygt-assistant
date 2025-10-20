import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

try:  # pragma: no cover - allow running without infra repos
    from infra.repos.factory import client_sessions_repo  # type: ignore
except Exception:  # pragma: no cover

    class _MemoryClientSessions:
        _rows = {}

        def create(self, *, user_id: str, token: str, expires_at: str) -> None:
            self._rows[token] = {"user_id": user_id, "expires_at": expires_at}

        def get(self, token: str):
            return self._rows.get(token)

    def client_sessions_repo():  # type: ignore
        return _MemoryClientSessions()


def _is_dev_mode() -> bool:
    return (
        os.getenv("DEV_MODE", "").strip().lower() in {"1", "true", "yes", "on"}
    ) or bool(os.getenv("PYTEST_CURRENT_TEST"))


def client_cookie_name() -> str:
    return os.getenv("CLIENT_COOKIE_NAME", "client_session")


def issue_client_session(user_id: str, ttl_minutes: int = 60 * 24 * 14) -> str:
    # In dev mode, prefer a deterministic token that survives API reloads
    if _is_dev_mode():
        return f"dev-{user_id}"
    token = secrets.token_urlsafe(48)
    expires = datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes)
    client_sessions_repo().create(
        user_id=user_id, token=token, expires_at=expires.isoformat()
    )
    return token


def verify_client_session(token: str) -> Optional[str]:
    if not token:
        return None
    # Accept dev token pattern without repo lookup
    if _is_dev_mode() and token.startswith("dev-"):
        return token.split("dev-", 1)[1] or None
    row = client_sessions_repo().get(token)
    if not row:
        return None
    exp = row.get("expires_at")
    if exp:
        try:
            if datetime.fromisoformat(exp) < datetime.now(timezone.utc):
                return None
        except Exception:
            pass
    return row.get("user_id")

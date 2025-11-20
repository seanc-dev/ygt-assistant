import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from infra.repos.factory import client_sessions_repo


def _is_dev_mode() -> bool:
    return os.getenv("DEV_MODE", "").strip().lower() in {"1", "true", "yes", "on"}


def client_cookie_name() -> str:
    return os.getenv("CLIENT_COOKIE_NAME", "client_session")


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def issue_client_session(user_id: str, ttl_minutes: int = 60 * 24 * 14) -> str:
    token = secrets.token_urlsafe(48)
    expires = datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes)
    client_sessions_repo().create(
        user_id=user_id, token_hash=_hash(token), expires_at=expires.isoformat()
    )
    return token


def verify_client_session(token: str) -> Optional[str]:
    if not token:
        return None
    row = client_sessions_repo().get(_hash(token))
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

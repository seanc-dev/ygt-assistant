from datetime import datetime, timedelta, timezone

from infra.repos.factory import client_sessions_repo
from utils import client_session


def test_issue_and_verify_session(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_STORE_PATH", str(tmp_path / "sessions.db"))
    client_sessions_repo.cache_clear()  # type: ignore

    token = client_session.issue_client_session("user-123", ttl_minutes=5)
    assert client_session.verify_client_session(token) == "user-123"


def test_expired_session_rejected(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_STORE_PATH", str(tmp_path / "sessions.db"))
    client_sessions_repo.cache_clear()  # type: ignore

    token = client_session.issue_client_session("user-123", ttl_minutes=0)
    # manually backdate expiry
    repo = client_sessions_repo()
    repo.create(
        token_hash=client_session._hash(token),  # type: ignore[attr-defined]
        user_id="user-123",
        expires_at=(datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat(),
    )
    assert client_session.verify_client_session(token) is None

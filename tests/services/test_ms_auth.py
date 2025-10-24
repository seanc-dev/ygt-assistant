from __future__ import annotations
from typing import Any, Dict
from datetime import datetime, timezone, timedelta
import types

import httpx

from services.ms_auth import needs_refresh, ensure_access_token_sync


def test_needs_refresh_past_and_skew():
    past = (datetime.now(timezone.utc) - timedelta(seconds=10)).isoformat()
    soon = (datetime.now(timezone.utc) + timedelta(seconds=30)).isoformat()
    assert needs_refresh(past) is True
    # default skew=120s, so 30s ahead still needs refresh
    assert needs_refresh(soon) is True


class _Resp:
    def __init__(self, status_code: int, data: Dict[str, Any]):
        self.status_code = status_code
        self._data = data

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("err", request=None, response=None)

    def json(self) -> Dict[str, Any]:
        return self._data


def test_ensure_access_token_sync_refresh(monkeypatch):
    # Patch httpx.Client.post to return a fake token
    def _fake_post(self, url: str, data: Dict[str, Any]):  # type: ignore[override]
        return _Resp(200, {"access_token": "NEW_TOKEN"})  # noqa: E701

    monkeypatch.setenv("MS_CLIENT_ID", "id")
    monkeypatch.setenv("MS_CLIENT_SECRET", "secret")
    monkeypatch.setenv("ENCRYPTION_KEY", "0" * 32)

    monkeypatch.setattr(httpx.Client, "post", _fake_post, raising=True)

    token_row = {"access_token": "", "refresh_token": "", "expiry": ""}
    tok = ensure_access_token_sync("user", token_row, "common")
    assert tok == "NEW_TOKEN"



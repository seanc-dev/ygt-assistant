from __future__ import annotations
from typing import Any, Dict
import asyncio
import httpx

from services.ms_auth import ensure_access_token


class _Resp:
    def __init__(self, status_code: int, data: Dict[str, Any]):
        self.status_code = status_code
        self._data = data

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("err", request=None, response=None)

    def json(self) -> Dict[str, Any]:
        return self._data


async def _fake_post(url: str, data: Dict[str, Any]):
    return _Resp(200, {"access_token": "ASYNC_TOKEN"})


def test_async_ensure_access_token(monkeypatch):
    monkeypatch.setenv("MS_CLIENT_ID", "id")
    monkeypatch.setenv("MS_CLIENT_SECRET", "secret")
    monkeypatch.setenv("ENCRYPTION_KEY", "0" * 32)

    async def _fake_post_method(self, url: str, data: Dict[str, Any]):  # type: ignore
        return _Resp(200, {"access_token": "ASYNC_TOKEN"})

    monkeypatch.setattr(httpx.AsyncClient, "post", _fake_post_method)

    token_row = {"access_token": "", "refresh_token": "", "expiry": ""}

    async def _run():
        tok = await ensure_access_token("user", token_row, "common")
        assert tok == "ASYNC_TOKEN"

    asyncio.run(_run())

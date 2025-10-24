from __future__ import annotations
from typing import Any, Dict
import httpx

from services.microsoft_calendar import MicrosoftCalendarProvider
from services.providers.errors import ProviderError


class _Resp:
    def __init__(self, status_code: int, data: Dict[str, Any]):
        self.status_code = status_code
        self._data = data

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("err", request=None, response=None)

    def json(self) -> Dict[str, Any]:
        return self._data


def test_create_and_delete_event(monkeypatch):
    prov = MicrosoftCalendarProvider("user")

    async def _fake_request(method: str, url: str, **kw: Any):  # type: ignore
        if method == "POST":
            return _Resp(
                201, {"id": "ev1", "webLink": "https://outlook.office.com/cal/ev1"}
            )
        return _Resp(204, {})

    async def _fake_auth():  # type: ignore
        return "TOKEN"

    monkeypatch.setattr(prov, "_request_with_retry", _fake_request)
    monkeypatch.setattr(prov, "_auth", _fake_auth)

    ev = prov.create_event({"subject": "S", "start": {}, "end": {}})
    assert ev["id"] == "ev1" and ev["webLink"].startswith("https://")
    prov.delete_event("ev1")


def test_calendar_retry_on_429(monkeypatch):
    prov = MicrosoftCalendarProvider("user")
    calls = {"n": 0}

    async def _fake_auth():  # type: ignore
        return "TOKEN"

    monkeypatch.setattr(prov, "_auth", _fake_auth)

    # Patch httpx.AsyncClient.request to simulate retries then success
    original_client = __import__("httpx").AsyncClient

    class _FakeClient(original_client):  # type: ignore
        async def request(self, method, url, **kw):  # type: ignore
            calls["n"] += 1
            code = 429 if calls["n"] < 3 else 201
            return _Resp(
                code, {"id": "ev2", "webLink": "https://outlook.office.com/cal/ev2"}
            )

    monkeypatch.setattr(__import__("httpx"), "AsyncClient", _FakeClient)

    ev = prov.create_event({"subject": "S", "start": {}, "end": {}})
    assert ev["id"] == "ev2"
    assert calls["n"] >= 3


def test_create_event_401_provider_error(monkeypatch):
    prov = MicrosoftCalendarProvider("user")

    async def _fake_auth():  # type: ignore
        return "TOKEN"

    original_client = __import__("httpx").AsyncClient

    class _FakeClient401(original_client):  # type: ignore
        async def request(self, method, url, **kw):  # type: ignore
            return _Resp(401, {})

    monkeypatch.setattr(prov, "_auth", _fake_auth)
    monkeypatch.setattr(__import__("httpx"), "AsyncClient", _FakeClient401)

    try:
        prov.create_event({"subject": "S", "start": {}, "end": {}})
        assert False, "expected ProviderError"
    except ProviderError as e:
        assert e.status_code == 401
        assert "Reconnect" in (e.hint or "")

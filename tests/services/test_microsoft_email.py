from __future__ import annotations
from typing import Any, Dict
import httpx
import types

from services.microsoft_email import MicrosoftEmailProvider


class _Resp:
    def __init__(self, status_code: int, data: Dict[str, Any]):
        self.status_code = status_code
        self._data = data

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("err", request=None, response=None)

    def json(self) -> Dict[str, Any]:
        return self._data


def test_list_inbox_maps_fields(monkeypatch):
    prov = MicrosoftEmailProvider("user")

    async def _fake_request(method: str, url: str, **kw: Any):  # type: ignore
        return _Resp(200, {
            "value": [
                {
                    "id": "1",
                    "subject": "Hello",
                    "from": {"emailAddress": {"address": "a@example.com"}},
                    "receivedDateTime": "2025-01-01T00:00:00Z",
                    "bodyPreview": "Hi",
                    "webLink": "https://outlook.office.com/mail/1",
                }
            ]
        })

    async def _fake_auth():  # type: ignore
        return "TOKEN"

    monkeypatch.setattr(prov, "_request_with_retry", _fake_request)
    monkeypatch.setattr(prov, "_auth", _fake_auth)

    items = prov.list_inbox(5)
    assert items and items[0]["id"] == "1" and items[0]["link"].startswith("https://")


def test_send_message_ok(monkeypatch):
    prov = MicrosoftEmailProvider("user")

    async def _fake_request(method: str, url: str, **kw: Any):  # type: ignore
        return _Resp(202, {})

    async def _fake_auth():  # type: ignore
        return "TOKEN"

    monkeypatch.setattr(prov, "_request_with_retry", _fake_request)
    monkeypatch.setattr(prov, "_auth", _fake_auth)

    res = prov.send_message(["a@example.com"], "S", "B")
    assert res["status"] == "sent"



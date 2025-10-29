from __future__ import annotations
from typing import Any, Dict, List
import os
import httpx

from services.providers.calendar_provider import CalendarProvider
from services.providers.errors import ProviderError
from services.ms_auth import (
    ensure_access_token,
    ensure_access_token_sync,
    token_store_from_env,
)
from utils.metrics import increment
import uuid
import asyncio
from settings import GRAPH_TIMEOUT_MS, GRAPH_RETRY_MAX


class MicrosoftCalendarProvider(CalendarProvider):
    def __init__(self, user_id: str, tenant_id: str | None = None) -> None:
        self.user_id = user_id
        self.tenant_id = tenant_id or os.getenv("MS_TENANT_ID", "common")

    def _base(self) -> str:
        return "https://graph.microsoft.com/v1.0"

    async def _auth(self) -> str:
        row = None
        try:
            store = token_store_from_env()
            row = store.get(self.user_id)
        except Exception:
            row = None
        if row:
            return ensure_access_token_sync(self.user_id, row, self.tenant_id)
        tok = os.getenv("MS_TEST_ACCESS_TOKEN", "")
        if tok:
            return tok
        raise ProviderError(
            "microsoft",
            "auth",
            "missing access token",
            hint="Connect Microsoft account",
        )

    async def _request_with_retry(
        self,
        method: str,
        url: str,
        *,
        headers: Dict[str, str],
        params: Dict[str, Any] | None = None,
        json: Any | None = None,
        expected_status: List[int] | None = None,
        timeout: float = 10.0,
    ) -> httpx.Response:
        expected = set(expected_status or [200])
        backoff = 0.5
        last_exc: Exception | None = None
        req_id = str(uuid.uuid4())
        h = {**headers, "x-ms-client-request-id": req_id}
        for attempt in range(max(1, GRAPH_RETRY_MAX)):
            try:
                async with httpx.AsyncClient(timeout=GRAPH_TIMEOUT_MS / 1000.0) as c:
                    r = await c.request(
                        method, url, params=params, json=json, headers=h
                    )
                if r.status_code in expected:
                    return r
                # Allow callers to translate 401 into ProviderError with reconnect hint
                if r.status_code == 401:
                    return r
                if r.status_code in (429,) or 500 <= r.status_code < 600:
                    increment(
                        "ms.cal.http.retry", status=r.status_code, attempt=attempt + 1
                    )
                    await asyncio.sleep(backoff)
                    backoff *= 2
                    continue
                r.raise_for_status()
                return r
            except Exception as exc:  # pragma: no cover - network
                last_exc = exc
                increment("ms.cal.http.exception", attempt=attempt + 1)
                await asyncio.sleep(backoff)
                backoff *= 2
        if last_exc:
            raise last_exc
        raise ProviderError("microsoft", "http", "unexpected failure")

    def list_events(self, time_min: str, time_max: str) -> List[Dict[str, Any]]:
        import anyio

        async def _run() -> List[Dict[str, Any]]:
            token = await self._auth()
            params = {
                "startDateTime": time_min,
                "endDateTime": time_max,
                "$select": "subject,start,end,location,onlineMeeting,webLink",
                "$orderby": "start/dateTime",
            }
            r = await self._request_with_retry(
                "GET",
                f"{self._base()}/me/calendarView",
                params=params,
                headers={"Authorization": f"Bearer {token}"},
                expected_status=[200],
            )
            items = r.json().get("value", [])
            increment("ms.cal.list_events.ok", n=len(items))
            return [
                {
                    "id": it.get("id"),
                    "title": it.get("subject"),
                    "start": (it.get("start") or {}).get("dateTime"),
                    "end": (it.get("end") or {}).get("dateTime"),
                    "link": it.get("webLink"),
                }
                for it in items
            ]

        return anyio.run(_run)

    def freebusy(self, time_min: str, time_max: str) -> Dict[str, Any]:
        # MVP: derive from list_events
        events = self.list_events(time_min, time_max)
        return {"busy": [{"start": e["start"], "end": e["end"]} for e in events]}

    def create_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        import anyio

        async def _run() -> Dict[str, Any]:
            token = await self._auth()
            payload = {
                "subject": event.get("title") or event.get("subject"),
                "start": {"dateTime": event.get("start"), "timeZone": "UTC"},
                "end": {"dateTime": event.get("end"), "timeZone": "UTC"},
                "location": {"displayName": (event.get("location") or "")},
            }
            r = await self._request_with_retry(
                "POST",
                f"{self._base()}/me/events",
                json=payload,
                headers={"Authorization": f"Bearer {token}"},
                expected_status=[201, 200],
            )
            if r.status_code == 401:
                raise ProviderError(
                    "microsoft",
                    "create_event",
                    "unauthorized",
                    status_code=401,
                    hint="Reconnect Microsoft",
                )
            increment("ms.cal.create_event.ok")
            return r.json()

        return anyio.run(_run)

    def create_events_batch(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for ev in events:
            results.append(self.create_event(ev))
        return results

    def update_event(self, event_id: str, patch: Dict[str, Any]) -> Dict[str, Any]:
        import anyio

        async def _run() -> Dict[str, Any]:
            token = await self._auth()
            r = await self._request_with_retry(
                "PATCH",
                f"{self._base()}/me/events/{event_id}",
                json=patch,
                headers={"Authorization": f"Bearer {token}"},
                expected_status=[200, 204],
            )
            increment("ms.cal.update_event.ok")
            return r.json() if r.content else {"id": event_id}

        return anyio.run(_run)

    def delete_event(self, event_id: str) -> Dict[str, Any]:
        import anyio

        async def _run() -> Dict[str, Any]:
            token = await self._auth()
            _ = await self._request_with_retry(
                "DELETE",
                f"{self._base()}/me/events/{event_id}",
                headers={"Authorization": f"Bearer {token}"},
                expected_status=[204, 200],
            )
            increment("ms.cal.delete_event.ok")
            return {"id": event_id, "deleted": True}

        return anyio.run(_run)

from __future__ import annotations
from typing import Any, Dict, List
import os
import httpx

from services.providers.calendar_provider import CalendarProvider
from services.providers.errors import ProviderError
from services.ms_auth import ensure_access_token, token_store_from_env


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
            return await ensure_access_token(self.user_id, row, self.tenant_id)
        tok = os.getenv("MS_TEST_ACCESS_TOKEN", "")
        if tok:
            return tok
        raise ProviderError(
            "microsoft",
            "auth",
            "missing access token",
            hint="Connect Microsoft account",
        )

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
            async with httpx.AsyncClient(timeout=10) as c:
                r = await c.get(
                    f"{self._base()}/me/calendarView",
                    params=params,
                    headers={"Authorization": f"Bearer {token}"},
                )
                r.raise_for_status()
                items = r.json().get("value", [])
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
            async with httpx.AsyncClient(timeout=10) as c:
                r = await c.post(
                    f"{self._base()}/me/events",
                    json=payload,
                    headers={"Authorization": f"Bearer {token}"},
                )
                r.raise_for_status()
                return r.json()

        return anyio.run(_run)

    def update_event(self, event_id: str, patch: Dict[str, Any]) -> Dict[str, Any]:
        import anyio

        async def _run() -> Dict[str, Any]:
            token = await self._auth()
            async with httpx.AsyncClient(timeout=10) as c:
                r = await c.patch(
                    f"{self._base()}/me/events/{event_id}",
                    json=patch,
                    headers={"Authorization": f"Bearer {token}"},
                )
                r.raise_for_status()
                return r.json() if r.content else {"id": event_id}

        return anyio.run(_run)

    def delete_event(self, event_id: str) -> Dict[str, Any]:
        import anyio

        async def _run() -> Dict[str, Any]:
            token = await self._auth()
            async with httpx.AsyncClient(timeout=10) as c:
                r = await c.delete(
                    f"{self._base()}/me/events/{event_id}",
                    headers={"Authorization": f"Bearer {token}"},
                )
                r.raise_for_status()
                return {"id": event_id, "deleted": True}

        return anyio.run(_run)

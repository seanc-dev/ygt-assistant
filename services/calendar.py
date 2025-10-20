from __future__ import annotations
from typing import Any, Dict, List
from datetime import datetime, timedelta, timezone

from services.providers.registry import get_calendar_provider


class CalendarService:
    """Shim delegating to the configured calendar provider."""

    def __init__(self, user_id: str | None = None) -> None:
        self._user_id = user_id or "default"

    def list_today(self) -> List[Dict[str, Any]]:
        prov = get_calendar_provider(self._user_id)
        now = datetime.now(timezone.utc)
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        return prov.list_events(start.isoformat(), end.isoformat())

    def create_or_update(self, event: Dict[str, Any]) -> Dict[str, Any]:
        prov = get_calendar_provider(self._user_id)
        if event.get("id"):
            return prov.update_event(
                event["id"], {k: v for k, v in event.items() if k != "id"}
            )
        return prov.create_event(event)

    def freebusy(self, when: Dict[str, Any]) -> Dict[str, Any]:
        prov = get_calendar_provider(self._user_id)
        return prov.freebusy(when.get("timeMin", ""), when.get("timeMax", ""))

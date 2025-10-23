from __future__ import annotations
from typing import Any, Dict, List
import json
import os

from services.providers.email_provider import EmailProvider
from services.providers.calendar_provider import CalendarProvider


def _load_fixture(path: str) -> Any:
    full = path
    if not os.path.isabs(full):
        full = os.path.join(os.getcwd(), "llm_testing", path)
    with open(full, "r") as f:
        return json.load(f)


class MockMicrosoftEmail(EmailProvider):
    def __init__(self, user_id: str, fixtures: Dict[str, str] | None = None) -> None:
        self.user_id = user_id
        self._fixtures = fixtures or {}
        self._drafts: Dict[str, Dict[str, Any]] = {}

    def list_threads(self, q: str, max_n: int) -> List[Dict[str, Any]]:
        data = _load_fixture(self._fixtures.get("mail", "fixtures/graph/inbox_small.json"))
        items = data.get("messages", [])[: max(1, min(max_n or 5, 50))]
        out: List[Dict[str, Any]] = []
        for it in items:
            out.append(
                {
                    "id": it.get("id"),
                    "subject": it.get("subject"),
                    "from": it.get("from"),
                    "to": it.get("to", []),
                    "received_at": it.get("received_at"),
                    "preview": it.get("preview"),
                    "link": it.get("link"),
                }
            )
        return out

    def create_draft(self, to: List[str], subject: str, body: str) -> Dict[str, Any]:
        draft_id = f"mock-{len(self._drafts)+1}"
        d = {"id": draft_id, "to": to, "subject": subject, "body": body, "status": "draft"}
        self._drafts[draft_id] = d
        return d

    def send_draft(self, draft_id: str) -> Dict[str, Any]:
        d = self._drafts.get(draft_id)
        if not d:
            return {"id": draft_id, "status": "missing"}
        d["status"] = "sent"
        return {"id": draft_id, "status": "sent"}

    def send_message(self, to: List[str], subject: str, body: str) -> Dict[str, Any]:
        return {"id": "send_mail", "status": "sent"}

    def get_message(self, message_id: str) -> Dict[str, Any]:
        data = _load_fixture(self._fixtures.get("mail", "fixtures/graph/inbox_small.json"))
        for it in data.get("messages", []):
            if it.get("id") == message_id:
                return it
        return {"id": message_id}


class MockMicrosoftCalendar(CalendarProvider):
    def __init__(self, user_id: str, fixtures: Dict[str, str] | None = None) -> None:
        self.user_id = user_id
        self._fixtures = fixtures or {}
        self._events: Dict[str, Dict[str, Any]] = {}

    def list_events(self, time_min: str, time_max: str) -> List[Dict[str, Any]]:
        data = _load_fixture(self._fixtures.get("calendar", "fixtures/graph/calendar_day_busy.json"))
        items = data.get("events", [])
        return [
            {
                "id": it.get("id"),
                "title": it.get("title"),
                "start": it.get("start"),
                "end": it.get("end"),
                "link": it.get("link"),
            }
            for it in items
        ]

    def freebusy(self, time_min: str, time_max: str) -> Dict[str, Any]:
        events = self.list_events(time_min, time_max)
        return {"busy": [{"start": e["start"], "end": e["end"]} for e in events]}

    def create_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        event_id = f"evt-{len(self._events)+1}"
        e = {"id": event_id, **event}
        self._events[event_id] = e
        return e

    def update_event(self, event_id: str, patch: Dict[str, Any]) -> Dict[str, Any]:
        e = self._events.get(event_id, {"id": event_id})
        e.update(patch)
        self._events[event_id] = e
        return e

    def delete_event(self, event_id: str) -> Dict[str, Any]:
        self._events.pop(event_id, None)
        return {"id": event_id, "deleted": True}



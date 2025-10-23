from __future__ import annotations
import os
import importlib

from services.providers.email_provider import EmailProvider
from services.providers.calendar_provider import CalendarProvider
from services.providers.mock_graph import (
    MockMicrosoftEmail,
    MockMicrosoftCalendar,
)


def _provider_from_env(var_name: str, default: str = "stub") -> str:
    return (os.getenv(var_name) or default).strip().lower()


# Simple stub implementations for initial wiring
class _StubEmail(EmailProvider):
    def list_threads(self, q: str, max_n: int):
        return []

    def create_draft(self, to, subject, body):
        return {"id": "stub-draft", "to": to, "subject": subject}

    def send_draft(self, draft_id: str):
        return {"id": draft_id, "status": "sent"}

    def send_message(self, to, subject, body):
        return {"id": "stub-message", "status": "sent"}

    def get_message(self, message_id: str):
        return {"id": message_id, "subject": "", "from": "", "to": []}


class _StubCalendar(CalendarProvider):
    def list_events(self, time_min: str, time_max: str):
        return []

    def freebusy(self, time_min: str, time_max: str):
        return {"busy": []}

    def create_event(self, event: dict):
        return {"id": "stub-event", **event}

    def update_event(self, event_id: str, patch: dict):
        return {"id": event_id, **patch}

    def delete_event(self, event_id: str):
        return {"id": event_id, "deleted": True}


def _is_true(v: str | None) -> bool:
    return (v or "").strip().lower() in {"1", "true", "yes", "on"}


def get_email_provider(user_id: str) -> EmailProvider:
    # CI/mock path: force mock providers when USE_MOCK_GRAPH=true
    if _is_true(os.getenv("USE_MOCK_GRAPH")):
        return MockMicrosoftEmail(user_id)
    name = _provider_from_env("PROVIDER_EMAIL", "microsoft")
    if name == "google":
        try:
            module = importlib.import_module("services.google_email")
            provider_cls = getattr(module, "GoogleEmailProvider", None)
            if provider_cls is None:
                return _StubEmail()
            return provider_cls(user_id)
        except (ModuleNotFoundError, ImportError):
            return _StubEmail()
    if name == "microsoft":
        try:
            module = importlib.import_module("services.microsoft_email")
            provider_cls = getattr(module, "MicrosoftEmailProvider", None)
            if provider_cls is None:
                return _StubEmail()
            return provider_cls(user_id)
        except (ModuleNotFoundError, ImportError):
            return _StubEmail()
    return _StubEmail()


def get_calendar_provider(user_id: str) -> CalendarProvider:
    if _is_true(os.getenv("USE_MOCK_GRAPH")):
        return MockMicrosoftCalendar(user_id)
    name = _provider_from_env("PROVIDER_CAL", "microsoft")
    if name == "google":
        try:
            module = importlib.import_module("services.google_calendar")
            provider_cls = getattr(module, "GoogleCalendarProvider", None)
            if provider_cls is None:
                return _StubCalendar()
            return provider_cls(user_id)
        except (ModuleNotFoundError, ImportError):
            return _StubCalendar()
    if name == "microsoft":
        try:
            module = importlib.import_module("services.microsoft_calendar")
            provider_cls = getattr(module, "MicrosoftCalendarProvider", None)
            if provider_cls is None:
                return _StubCalendar()
            return provider_cls(user_id)
        except (ModuleNotFoundError, ImportError):
            return _StubCalendar()
    return _StubCalendar()

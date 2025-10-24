from __future__ import annotations
import os
from services.providers.registry import (
    get_email_provider as _real_email,
    get_calendar_provider as _real_cal,
)
from services.providers.mock_graph import MockMicrosoftEmail, MockMicrosoftCalendar
from settings import (
    FEATURE_GRAPH_LIVE,
    FEATURE_LIVE_LIST_INBOX,
    FEATURE_LIVE_SEND_MAIL,
    FEATURE_LIVE_CREATE_EVENTS,
)


def _is_true(v: str | None) -> bool:
    return (v or "").strip().lower() in {"1", "true", "yes", "on"}


def get_email_provider(user_id: str):
    if _is_true(os.getenv("USE_MOCK_GRAPH")):
        return MockMicrosoftEmail(user_id)
    return _real_email(user_id)


def get_calendar_provider(user_id: str):
    if _is_true(os.getenv("USE_MOCK_GRAPH")):
        return MockMicrosoftCalendar(user_id)
    return _real_cal(user_id)


def get_email_provider_for(action: str, user_id: str):
    if not FEATURE_GRAPH_LIVE:
        return MockMicrosoftEmail(user_id)
    if action == "list_inbox" and FEATURE_LIVE_LIST_INBOX:
        return _real_email(user_id)
    if action == "send_mail" and FEATURE_LIVE_SEND_MAIL:
        return _real_email(user_id)
    return MockMicrosoftEmail(user_id)


def get_calendar_provider_for(action: str, user_id: str):
    if not FEATURE_GRAPH_LIVE:
        return MockMicrosoftCalendar(user_id)
    if action == "create_events" and FEATURE_LIVE_CREATE_EVENTS:
        return _real_cal(user_id)
    return MockMicrosoftCalendar(user_id)

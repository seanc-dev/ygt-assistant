from __future__ import annotations
import os
from services.providers.registry import (
    get_email_provider as _real_email,
    get_calendar_provider as _real_cal,
)
from services.providers.mock_graph import MockMicrosoftEmail, MockMicrosoftCalendar


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

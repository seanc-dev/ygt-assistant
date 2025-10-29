from __future__ import annotations
from presentation.api.deps.providers import (
    get_email_provider_for,
    get_calendar_provider_for,
)
import presentation.api.deps.providers as prov_mod
from services.providers.mock_graph import MockMicrosoftEmail, MockMicrosoftCalendar


def test_routing_prefers_mocks_in_ci(monkeypatch):
    monkeypatch.setenv("USE_MOCK_GRAPH", "true")
    e = get_email_provider_for("list_inbox", "u")
    c = get_calendar_provider_for("create_events", "u")
    assert isinstance(e, MockMicrosoftEmail)
    assert isinstance(c, MockMicrosoftCalendar)


def test_routing_requires_global_and_action_flags(monkeypatch):
    # Force mocks if env dictates
    monkeypatch.setenv("USE_MOCK_GRAPH", "true")
    e = get_email_provider_for("list_inbox", "u")
    assert isinstance(e, MockMicrosoftEmail)

    # Global on but per-action off -> mock
    monkeypatch.setenv("FEATURE_GRAPH_LIVE", "true")
    monkeypatch.setenv("FEATURE_LIVE_LIST_INBOX", "false")
    monkeypatch.setattr(prov_mod, "FEATURE_GRAPH_LIVE", True, raising=False)
    monkeypatch.setattr(prov_mod, "FEATURE_LIVE_LIST_INBOX", False, raising=False)
    e2 = get_email_provider_for("list_inbox", "u")
    assert isinstance(e2, MockMicrosoftEmail)

    # Global on and per-action on -> expect real provider
    monkeypatch.delenv("USE_MOCK_GRAPH", raising=False)
    monkeypatch.setenv("FEATURE_LIVE_LIST_INBOX", "true")
    monkeypatch.setattr(prov_mod, "FEATURE_GRAPH_LIVE", True, raising=False)
    monkeypatch.setattr(prov_mod, "FEATURE_LIVE_LIST_INBOX", True, raising=False)
    e3 = get_email_provider_for("list_inbox", "u")
    assert not isinstance(e3, MockMicrosoftEmail)

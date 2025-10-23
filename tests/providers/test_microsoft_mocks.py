from __future__ import annotations
import os
from services.providers.mock_graph import MockMicrosoftEmail, MockMicrosoftCalendar


def test_mock_email_list_threads_reads_fixture(tmp_path):
    os.environ["USE_MOCK_GRAPH"] = "true"
    p = MockMicrosoftEmail("u1", fixtures={"mail": "fixtures/graph/inbox_small.json"})
    items = p.list_threads("", 5)
    assert isinstance(items, list)
    assert items, "should load messages from fixture"


def test_mock_calendar_list_events_reads_fixture(tmp_path):
    os.environ["USE_MOCK_GRAPH"] = "true"
    p = MockMicrosoftCalendar("u1", fixtures={"calendar": "fixtures/graph/calendar_day_busy.json"})
    items = p.list_events("2025-01-01T00:00:00Z", "2025-01-02T00:00:00Z")
    assert isinstance(items, list)
    assert items, "should load events from fixture"



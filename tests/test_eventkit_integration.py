import pytest
from datetime import datetime
import calendar_agent_eventkit
from calendar_agent_eventkit import (
    create_event,
    delete_event,
    move_event,
    add_notification,
)
from calendar_agent_eventkit import _agent
import re


@pytest.fixture(autouse=True)
def dummy_store(monkeypatch):
    """Replace the EventKit store with a dummy for integration testing."""

    class DummyStore:
        def __init__(self):
            self.saved_events = []

        def saveEvent_span_error_(self, event, span, error_ptr):
            "Simulate successful save and record the event"
            self.saved_events.append(event)
            return True

        def removeEvent_span_error_(self, event, span, error_ptr):
            "Simulate successful delete"
            return True

        def predicateForEventsWithStartDate_endDate_calendars_(self, s, e, c):
            "Simulate predicate"
            return "dummy_predicate"

        def eventsMatchingPredicate_(self, pred):
            "Return recorded events"
            return self.saved_events

    dummy = DummyStore()
    monkeypatch.setattr(calendar_agent_eventkit._agent, "store", dummy)

    # Stub EKEvent and span constant to avoid PyObjC bridging
    class DummyEvent:
        def __init__(self):
            self.title = None
            self.startDate = None

        @classmethod
        def eventWithEventStore_(cls, store):
            return cls()

        # Add setter stubs for EventKit properties
        def setTitle_(self, title):
            self.title = title

        def setStartDate_(self, date):
            self.startDate = date

        def setEndDate_(self, date):
            pass

        def setLocation_(self, location):
            pass

    monkeypatch.setattr(calendar_agent_eventkit, "EKEvent", DummyEvent)
    monkeypatch.setattr(calendar_agent_eventkit, "EKSpanThisEvent", 0)
    return dummy


class TestCreateEventIntegration:
    def test_create_event_missing_fields(self):
        res = create_event({})
        assert not res["success"]

    def test_create_event_access_denied(self, monkeypatch):
        # Simulate save failure
        def fake_save(event, span, error_ptr):
            return False

        monkeypatch.setattr(_agent.store, "saveEvent_span_error_", fake_save)
        details = {
            "title": "Meeting",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": "10:00",
            "duration": 30,
        }
        res = create_event(details)
        assert not res["success"]

    def test_create_event_success(self):
        details = {
            "title": "Meeting",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": "10:00",
            "duration": 30,
        }
        res = create_event(details)
        assert res["success"]


class TestDeleteEventIntegration:
    def test_delete_event_missing_fields(self):
        res = delete_event({})
        assert not res["success"]

    def test_delete_event_success(self):
        details = {
            "title": "Meeting",
            "date": datetime.now().strftime("%Y-%m-%d"),
        }
        res = delete_event(details)
        assert res["success"]

    def test_delete_event_invalid_date(self):
        res = delete_event({"title": "Meeting", "date": "invalid"})
        assert not res["success"]


class TestMoveEventIntegration:
    def test_move_event_missing_fields(self):
        res = move_event({})
        assert not res["success"]

    def test_move_event_success(self):
        today = datetime.now().strftime("%Y-%m-%d")
        details = {
            "title": "Meeting",
            "old_date": today,
            "new_date": today,
            "new_time": "11:00",
        }
        res = move_event(details)
        assert res["success"]

    def test_move_event_invalid_old_date(self):
        today = datetime.now().strftime("%Y-%m-%d")
        res = move_event(
            {
                "title": "Meeting",
                "old_date": "invalid",
                "new_date": today,
                "new_time": "11:00",
            }
        )
        assert not res["success"]


class TestAddNotificationIntegration:
    def test_add_notification_missing_fields(self):
        res = add_notification({})
        assert not res["success"]

    def test_add_notification_success(self):
        details = {
            "title": "Meeting",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "minutes_before": 15,
        }
        res = add_notification(details)
        assert res["success"]

    def test_add_notification_invalid_minutes(self):
        today = datetime.now().strftime("%Y-%m-%d")
        res = add_notification(
            {"title": "Meeting", "date": today, "minutes_before": "15"}
        )
        assert not res["success"]


# New integration test for listing events after creation
class TestListEventsIntegration:
    def test_list_event_after_creation(self):
        today = datetime.now().strftime("%Y-%m-%d")
        details = {
            "title": "IntegrationTestEvent",
            "date": today,
            "time": "12:00",
            "duration": 30,
        }
        # Create the event
        res_create = create_event(details)
        assert res_create[
            "success"
        ], f"Failed to create event: {res_create.get('error')}"
        # List events for that date
        res_list = calendar_agent_eventkit.list_events_and_reminders(today, today)
        events = res_list.get("events", [])
        # Ensure the event string includes the title and timestamp
        pattern = rf"IntegrationTestEvent \| {today} 12:00:00"
        assert any(
            re.match(pattern, e) for e in events
        ), f"Event did not match pattern {pattern}, got {events}"

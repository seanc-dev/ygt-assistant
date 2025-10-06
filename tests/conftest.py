import os

import pytest
import calendar_agent_eventkit


TEST_ADMIN_SECRET = "test-admin-secret-1234567890"
TEST_ENCRYPTION_KEY = "D_Jhyl9DGCCyOLU_qTzw3CSLinmvglzsXDbNSsmw24w="

os.environ.setdefault("TESTING", "true")
os.environ.setdefault("ADMIN_EMAIL", "admin@example.com")
os.environ.setdefault("ADMIN_SECRET", TEST_ADMIN_SECRET)
os.environ.setdefault("ENCRYPTION_KEY", TEST_ENCRYPTION_KEY)
os.environ.setdefault("NYLAS_API_URL", "https://login.nylas.com")


@pytest.fixture(autouse=True)
def dummy_store(monkeypatch):
    """Stub the EventKit store for all tests."""

    class DummyStore:
        def __init__(self):
            self.saved_events = []

        def saveEvent_span_error_(self, event, span, error_ptr):
            self.saved_events.append(event)
            return True

        def removeEvent_span_error_(self, event, span, error_ptr):
            return True

        def predicateForEventsWithStartDate_endDate_calendars_(self, s, e, c):
            return "dummy_pred"

        def eventsMatchingPredicate_(self, pred):
            return self.saved_events

    dummy = DummyStore()
    monkeypatch.setattr(calendar_agent_eventkit._agent, "store", dummy)

    # Stub EKEvent and span constant
    class DummyEvent:
        @classmethod
        def eventWithEventStore_(cls, store):
            return cls()

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

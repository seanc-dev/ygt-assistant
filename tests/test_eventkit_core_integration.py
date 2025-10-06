"""Integration tests for EventKit core functionality."""

import calendar_agent_eventkit


def test_list_events_and_reminders():
    """Test listing events and reminders."""
    result = calendar_agent_eventkit.list_events_and_reminders()
    assert isinstance(result, dict)
    assert "events" in result
    assert "reminders" in result
    assert isinstance(result["events"], list)
    assert isinstance(result["reminders"], list)


def test_create_event():
    """Test creating an event."""
    details = {
        "title": "Test Event",
        "date": "2024-01-01",
        "time": "14:00",
        "duration": 60,
    }
    result = calendar_agent_eventkit.create_event(details)
    assert isinstance(result, dict)
    assert "success" in result


def test_delete_event():
    """Test deleting an event."""
    details = {"title": "Test Event", "date": "2024-01-01"}
    result = calendar_agent_eventkit.delete_event(details)
    assert isinstance(result, dict)
    assert "success" in result


def test_move_event():
    """Test moving an event."""
    details = {
        "title": "Test Event",
        "old_date": "2024-01-01",
        "new_date": "2024-01-02",
        "new_time": "15:00",
    }
    result = calendar_agent_eventkit.move_event(details)
    assert isinstance(result, dict)
    assert "success" in result


def test_add_notification():
    """Test adding a notification."""
    details = {
        "title": "Test Event",
        "date": "2024-01-01",
        "minutes_before": 15,
    }
    result = calendar_agent_eventkit.add_notification(details)
    assert isinstance(result, dict)
    assert "success" in result

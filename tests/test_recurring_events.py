# pylint: skip-file
# type: ignore
"""Test recurring events functionality."""

from calendar_agent_eventkit import create_event, list_events_and_reminders


def test_create_recurring_daily():
    """Test creating a daily recurring event."""
    details = {
        "title": "Daily Standup",
        "date": "2024-01-01",
        "time": "09:00",
        "duration": 30,
        "recurrence_rule": "FREQ=DAILY;COUNT=5",
    }
    result = create_event(details)
    assert result["success"] is True


def test_list_recurring_daily():
    """Test listing daily recurring events."""
    # Create a daily recurring event
    details = {
        "title": "Daily Standup",
        "date": "2024-01-01",
        "time": "09:00",
        "duration": 30,
        "recurrence_rule": "FREQ=DAILY;COUNT=5",
    }
    create_event(details)
    # List events for the first 3 days
    result = list_events_and_reminders("2024-01-01", "2024-01-03")
    assert "Daily Standup" in str(result["events"])
    # Should have 3 occurrences
    assert len([e for e in result["events"] if "Daily Standup" in e]) == 3


def test_delete_recurring_series():
    """Test deleting an entire recurring series."""
    # Create a daily recurring event
    details = {
        "title": "Daily Standup",
        "date": "2024-01-01",
        "time": "09:00",
        "duration": 30,
        "recurrence_rule": "FREQ=DAILY;COUNT=5",
    }
    create_event(details)
    # Delete the entire series
    delete_details = {
        "title": "Daily Standup",
        "date": "2024-01-01",
        "delete_series": True,
    }
    from calendar_agent_eventkit import delete_event

    result = delete_event(delete_details)
    assert result["success"] is True
    # Verify no events remain
    list_result = list_events_and_reminders("2024-01-01", "2024-01-05")
    assert len([e for e in list_result["events"] if "Daily Standup" in e]) == 0


def test_delete_recurring_occurrence():
    """Test deleting a single occurrence of a recurring event."""
    # Create a daily recurring event
    details = {
        "title": "Daily Standup",
        "date": "2024-01-01",
        "time": "09:00",
        "duration": 30,
        "recurrence_rule": "FREQ=DAILY;COUNT=5",
    }
    create_event(details)
    # Delete just the first occurrence
    delete_details = {
        "title": "Daily Standup",
        "date": "2024-01-01",
        "delete_series": False,
    }
    from calendar_agent_eventkit import delete_event

    result = delete_event(delete_details)
    assert result["success"] is True
    # Verify only 4 events remain (5 - 1 deleted)
    list_result = list_events_and_reminders("2024-01-01", "2024-01-05")
    assert len([e for e in list_result["events"] if "Daily Standup" in e]) == 4

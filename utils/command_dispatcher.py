"""Command dispatcher for main loop actions."""

import re
import sys
from settings import USE_PORTS

try:
    from adapters.eventkit_calendar import EventKitCalendarAdapter

    _calendar_port = EventKitCalendarAdapter()
except Exception:
    _calendar_port = None
from calendar_agent_eventkit import (
    list_events_and_reminders,
    create_event,
    delete_event,
    move_event,
    add_notification,
)
from utils.cli_output import (
    format_events,
    format_reminders,
    print_events_and_reminders,
    format_error_message,
    format_success_message,
)


def handle_list_todays_events(details):
    """Handle listing today's events and reminders."""
    result = list_events_and_reminders(
        details.get("start_date"), details.get("end_date")
    )
    if result.get("error"):
        print(format_error_message(result["error"]))
        return
    print_events_and_reminders(result.get("events", []), result.get("reminders", []))


def handle_list_all(details):
    # Alias for list_todays_events
    handle_list_todays_events(details)


def handle_list_events_only(details):
    """Handle listing only events."""
    result = list_events_and_reminders(
        details.get("start_date"), details.get("end_date")
    )
    if result.get("error"):
        print(format_error_message(result["error"]))
        return
    print(format_events(result.get("events", [])))


def handle_list_reminders_only(details):
    """Handle listing only reminders."""
    result = list_events_and_reminders(
        details.get("start_date"), details.get("end_date")
    )
    if result.get("error"):
        print(format_error_message(result["error"]))
        return
    print(format_reminders(result.get("reminders", [])))


def handle_create_event(details):
    """Handle creating a new event."""
    # Prompt for duration if not provided
    if "duration" not in details or details.get("duration") is None:
        # Avoid interactive prompts under test or non-interactive sessions
        if "pytest" in sys.modules or not sys.stdin.isatty():
            details["duration"] = 60
        else:
            resp = input(
                "Duration not specified. Is one hour enough? (enter minutes e.g. 15 or press Enter for 60): "
            )
            resp_str = resp.strip()
            if resp_str:
                try:
                    details["duration"] = int(resp_str)
                except ValueError:
                    m = re.search(r"(\d+)", resp_str)
                    if m:
                        details["duration"] = int(m.group(1))
                    else:
                        print("Invalid duration; defaulting to 60 minutes.")
                        details["duration"] = 60
            else:
                details["duration"] = 60
    result = create_event(details)
    if result.get("success"):
        print(format_success_message(result.get("message")))
    else:
        print(format_error_message(result.get("error")))


def handle_delete_event(details):
    """Handle deleting an event."""
    result = delete_event(details)
    if result.get("success"):
        print(format_success_message(result.get("message")))
    else:
        print(format_error_message(result.get("error")))


def handle_move_event(details):
    """Handle moving/rescheduling an event."""
    result = move_event(details)
    if result.get("success"):
        print(format_success_message(result.get("message")))
    else:
        print(format_error_message(result.get("error")))


def handle_add_notification(details):
    """Handle adding a notification to an event."""
    result = add_notification(details)
    if result.get("success"):
        print(format_success_message(result.get("message")))
    else:
        print(format_error_message(result.get("error")))


# Map actions to handlers
HANDLERS = {
    "list_todays_events": handle_list_todays_events,
    "list_all": handle_list_all,
    "list_events_only": handle_list_events_only,
    "list_reminders_only": handle_list_reminders_only,
    "create_event": handle_create_event,
    "delete_event": handle_delete_event,
    "move_event": handle_move_event,
    "add_notification": handle_add_notification,
}


def dispatch(action: str, details: dict):
    """Dispatch the given action to the appropriate handler.

    When USE_PORTS is true and a CalendarPort adapter is available, route select
    calendar actions through the adapter. Otherwise, fallback to legacy handlers.
    """

    if (
        USE_PORTS
        and _calendar_port
        and action in {"create_event", "move_event", "delete_event"}
    ):
        try:
            if action == "create_event":
                return _calendar_port.create_event(details)
            if action == "move_event":
                return _calendar_port.move_event(details)
            if action == "delete_event":
                return _calendar_port.delete_event(details)
        except Exception as exc:
            # If adapter fails, surface error similar to handlers
            return {"success": False, "error": str(exc)}

    if action not in HANDLERS:
        raise KeyError(f"Unknown action: {action}")
    return HANDLERS[action](details)

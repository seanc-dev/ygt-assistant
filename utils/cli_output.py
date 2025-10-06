"""CLI output formatting helpers for the calendar assistant."""

from typing import List, Dict, Any, Optional
import os
import json
from datetime import datetime


def format_events(events: List[Dict[str, Any]]) -> str:
    """
    Format a list of calendar events for display.

    Args:
        events: List of event dictionaries with keys like 'title', 'start_date', 'end_date', etc.

    Returns:
        Formatted string representation of events

    Example:
        >>> events = [{'title': 'Team Meeting', 'start_date': '2024-01-15 10:00:00'}]
        >>> format_events(events)
        '📅 Team Meeting (10:00 AM)'
    """
    if not events:
        return "📅 Events:\n  - (none)"

    # Backward-compatibility: accept a list of strings and render with a header
    if events and isinstance(events[0], str):  # type: ignore[index]
        lines = ["📅 Events:"]
        lines.extend([f"  - {event}" for event in events])  # type: ignore[union-attr]
        return "\n".join(lines)

    formatted_events = []
    for event in events:
        title = event.get("title", "Untitled Event")
        start_date = event.get("start_date")
        end_date = event.get("end_date")

        # Format time
        time_str = ""
        if start_date:
            try:
                if isinstance(start_date, str):
                    dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
                else:
                    dt = start_date
                time_str = f" ({dt.strftime('%I:%M %p')})"
            except (ValueError, AttributeError):
                time_str = ""

        # Add duration if available
        duration_str = ""
        if start_date and end_date:
            try:
                if isinstance(start_date, str):
                    start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
                else:
                    start_dt = start_date
                if isinstance(end_date, str):
                    end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                else:
                    end_dt = end_date
                duration_minutes = int((end_dt - start_dt).total_seconds() / 60)
                if duration_minutes != 60:  # Don't show "60 minutes"
                    duration_str = f" ({duration_minutes}min)"
            except (ValueError, AttributeError):
                pass

        formatted_events.append(f"📅 {title}{time_str}{duration_str}")

    return "\n".join(formatted_events)


def format_reminders(reminders: List[Dict[str, Any]]) -> str:
    """
    Format a list of reminders/tasks for display.

    Args:
        reminders: List of reminder dictionaries with keys like 'title', 'due_date', etc.

    Returns:
        Formatted string representation of reminders

    Example:
        >>> reminders = [{'title': 'Review budget', 'due_date': '2024-01-15'}]
        >>> format_reminders(reminders)
        '✅ Review budget (Due: Jan 15)'
    """
    if not reminders:
        return "⏰ Reminders:\n  - (none)"

    # Backward-compatibility: accept a list of strings and render with a header
    if reminders and isinstance(reminders[0], str):  # type: ignore[index]
        lines = ["⏰ Reminders:"]
        lines.extend([f"  - {reminder}" for reminder in reminders])  # type: ignore[union-attr]
        return "\n".join(lines)

    formatted_reminders = []
    for reminder in reminders:
        title = reminder.get("title", "Untitled Reminder")
        due_date = reminder.get("due_date")

        # Format due date
        due_str = ""
        if due_date:
            try:
                if isinstance(due_date, str):
                    dt = datetime.fromisoformat(due_date.replace("Z", "+00:00"))
                else:
                    dt = due_date
                due_str = f" (Due: {dt.strftime('%b %d')})"
            except (ValueError, AttributeError):
                pass

        formatted_reminders.append(f"✅ {title}{due_str}")

    return "\n".join(formatted_reminders)


def print_events_and_reminders(
    events: List[Dict[str, Any]], reminders: List[Dict[str, Any]]
) -> None:
    """
    Print formatted events and reminders to the console.

    Args:
        events: List of event dictionaries
        reminders: List of reminder dictionaries

    Example:
        >>> events = [{'title': 'Team Meeting', 'start_date': '2024-01-15 10:00:00'}]
        >>> reminders = [{'title': 'Review budget', 'due_date': '2024-01-15'}]
        >>> print_events_and_reminders(events, reminders)
        📅 Today's Schedule:
        📅 Team Meeting (10:00 AM)

        ✅ Today's Reminders:
        ✅ Review budget (Due: Jan 15)
    """
    print("📅 Today's Schedule:")
    print(format_events(events))

    if reminders:
        print("\n✅ Today's Reminders:")
        print(format_reminders(reminders))


def format_error_message(error: str, suggestion: Optional[str] = None) -> str:
    """
    Format an error message with optional suggestion.

    Args:
        error: The error message
        suggestion: Optional suggestion for how to fix the error

    Returns:
        Formatted error message

    Example:
        >>> format_error_message("Invalid date format", "Use YYYY-MM-DD")
        '❌ Error: Invalid date format\n💡 Suggestion: Use YYYY-MM-DD'
    """
    formatted = f"❌ Error: {error}"
    if suggestion:
        formatted += f"\n💡 Suggestion: {suggestion}"
    return formatted


def format_success_message(message: str) -> str:
    """
    Format a success message.

    Args:
        message: The success message

    Returns:
        Formatted success message

    Example:
        >>> format_success_message("Event created successfully")
        '✅ Event created successfully'
    """
    return f"✅ {message}"


def format_clarification_question(question: str, context: Optional[str] = None) -> str:
    """
    Format a clarification question for the user.

    Args:
        question: The question to ask
        context: Optional context about why clarification is needed

    Returns:
        Formatted clarification question

    Example:
        >>> format_clarification_question("Which Monday?", "There are multiple Mondays this month")
        '🤔 Which Monday?\n📝 Context: There are multiple Mondays this month'
    """
    formatted = f"🤔 {question}"
    if context:
        formatted += f"\n📝 Context: {context}"
    return formatted


def render_pretty(payload: Dict[str, Any]) -> str:
    """Render a human-friendly string for CLI display.

    Supports minimal pretty rendering for common types; falls back to JSON.
    """

    t = payload.get("type")
    if t == "find_events":
        events: List[Dict[str, Any]] = payload.get("result", [])
        if not events:
            return "📆 No events found"
        return "\n".join(
            [f"• {e.get('title','(untitled)')} @ {e.get('start','')}" for e in events]
        )
    return json.dumps(payload, ensure_ascii=False)


def render(payload: Dict[str, Any]) -> str:
    """Return CLI-safe string in JSON or pretty mode based on CLI_OUTPUT_MODE.

    Default is 'json' for tests and API-first workflows.
    """

    mode = os.getenv("CLI_OUTPUT_MODE", "json").lower()
    if mode == "pretty":
        return render_pretty(payload)
    return json.dumps(payload, ensure_ascii=False)

import re
from utils.date_utils import parse_date_string
from typing import Optional, Dict, Any


def parse_list_range(cmd: str) -> Optional[Dict[str, Any]]:
    """Parse 'list events from START to END' and return {'start_date': str, 'end_date': str} or None."""
    m = re.search(r"list events from\s+(\S+)\s+to\s+(\S+)", cmd, re.IGNORECASE)
    if m:
        return {
            "start_date": parse_date_string(m.group(1)),
            "end_date": parse_date_string(m.group(2)),
        }
    return None


def parse_schedule_event(cmd: str) -> Optional[Dict[str, Any]]:
    """Parse 'schedule TITLE on DATE at TIME for DURATION minutes' into event creation details or None."""
    m = re.match(
        r"schedule\s+(.+?)\s+on\s+(\S+)\s+at\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\s+for\s*(\d+)\s*minutes",
        cmd,
        re.IGNORECASE,
    )
    if m:
        title, date_raw, time_raw, duration = (
            m.group(1),
            m.group(2),
            m.group(3),
            m.group(4),
        )
        date = parse_date_string(date_raw)
        # Normalize time to HH:MM
        tm = re.match(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", time_raw, re.IGNORECASE)
        if tm:
            hour = int(tm.group(1))
            minute = int(tm.group(2) or 0)
            ampm = tm.group(3).lower() if tm.group(3) else None
            if ampm:
                if ampm == "pm" and hour < 12:
                    hour += 12
                if ampm == "am" and hour == 12:
                    hour = 0
            time_str = f"{hour:02d}:{minute:02d}"
        else:
            time_str = time_raw
        return {
            "title": title.strip(),
            "date": date,
            "time": time_str,
            "duration": int(duration),
        }
    return None


def parse_delete_event(cmd: str) -> Optional[Dict[str, Any]]:
    """Parse 'delete TITLE on DATE' into deletion details or None."""
    m = re.match(r"delete\s+(.+?)\s+on\s+(\S+)", cmd, re.IGNORECASE)
    if m:
        title, date_raw = m.group(1).strip(), m.group(2)
        date = parse_date_string(date_raw)
        return {"title": title, "date": date}
    return None


def parse_move_event(cmd: str) -> Optional[Dict[str, Any]]:
    """Parse 'move TITLE on OLD_DATE to NEW_DATE at NEW_TIME' into move details or None."""
    m = re.match(
        r"move\s+(.+?)\s+on\s+(\S+)\s+to\s+(\S+)\s+at\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)",
        cmd,
        re.IGNORECASE,
    )
    if m:
        title, old_raw, new_raw, time_raw = (
            m.group(1).strip(),
            m.group(2),
            m.group(3),
            m.group(4),
        )
        old_date = parse_date_string(old_raw)
        new_date = parse_date_string(new_raw)
        tm = re.match(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", time_raw, re.IGNORECASE)
        if tm:
            hour = int(tm.group(1))
            minute = int(tm.group(2) or 0)
            ampm = tm.group(3).lower() if tm.group(3) else None
            if ampm:
                if ampm == "pm" and hour < 12:
                    hour += 12
                if ampm == "am" and hour == 12:
                    hour = 0
            new_time = f"{hour:02d}:{minute:02d}"
        else:
            new_time = time_raw
        return {
            "title": title,
            "old_date": old_date,
            "new_date": new_date,
            "new_time": new_time,
        }
    return None


def parse_add_notification(cmd: str) -> Optional[Dict[str, Any]]:
    """Parse 'add notification to TITLE on DATE MIN minutes before' into reminder details or None."""
    m = re.match(
        r"add\s+notification\s+to\s+(.+?)\s+on\s+(\S+)\s+(\d+)\s+minutes?\s+before",
        cmd,
        re.IGNORECASE,
    )
    if m:
        title, date_raw, minutes = m.group(1).strip(), m.group(2), int(m.group(3))
        date = parse_date_string(date_raw)
        return {"title": title, "date": date, "minutes_before": minutes}
    return None


def parse_single_date_list(cmd: str) -> Optional[Dict[str, Any]]:
    """Parse 'events for/on DATE' into a single-date list query or None."""
    m = re.search(r"events?\s+(?:for|on)\s+(\S+)", cmd, re.IGNORECASE)
    if m:
        date = parse_date_string(m.group(1))
        return {"start_date": date, "end_date": date}
    return None


def parse_command(cmd: str):
    """
    Try all explicit rule-based parsers in order; if none match, fall back to generic verb-based parsing.
    Returns a dict with keys 'action' and 'details'.
    """
    # Explicit regex-based parsers
    for parser, action in [
        (parse_list_range, "list_events_only"),
        (parse_schedule_event, "create_event"),
        (parse_delete_event, "delete_event"),
        (parse_move_event, "move_event"),
        (parse_add_notification, "add_notification"),
        (parse_single_date_list, "list_events_only"),
    ]:
        details = parser(cmd)
        if details:
            return {"action": action, "details": details}
    # Generic verb-based fallback
    lower = cmd.lower()
    if any(k in lower for k in ("delete", "cancel", "remove")):
        return {"action": "delete_event", "details": {}}
    if any(k in lower for k in ("move", "reschedule", "shift")):
        return {"action": "move_event", "details": {}}
    if any(k in lower for k in ("schedule", "create", "add", "book")):
        return {"action": "create_event", "details": {}}
    if "reminder" in lower or "task" in lower:
        return {"action": "list_reminders_only", "details": {}}
    if "event" in lower:
        return {"action": "list_events_only", "details": {}}
    if "today" in lower or "on" in lower:
        return {"action": "list_all", "details": {}}
    # Unknown command
    return {"action": "unknown", "details": {}}

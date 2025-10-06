from datetime import datetime, timedelta

# Mapping from weekday names to Python's weekday index (Monday=0)
WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


def next_weekday(day_name: str, from_date: datetime = None) -> datetime:
    """
    Return the next date for the given weekday name relative to from_date (or today).
    If from_date falls on the target weekday, returns one week later.
    """
    if from_date is None:
        from_date = datetime.now()
    name = day_name.strip().lower()
    if name not in WEEKDAYS:
        raise ValueError(f"Unknown weekday name: {day_name}")
    target = WEEKDAYS[name]
    days_ahead = (target - from_date.weekday() + 7) % 7
    if days_ahead == 0:
        days_ahead = 7
    return from_date + timedelta(days=days_ahead)


def parse_date_string(date_str: str, from_date: datetime = None) -> str:
    """
    Parse a date string and return an ISO date (YYYY-MM-DD). Supported inputs:
      - ISO strings YYYY-MM-DD
      - 'tomorrow'
      - Weekday names (e.g., 'Friday')
    Raises ValueError for invalid formats.
    """
    if from_date is None:
        from_date = datetime.now()
    s = date_str.strip().lower()
    if s == "tomorrow":
        return (from_date + timedelta(days=1)).strftime("%Y-%m-%d")
    if s in WEEKDAYS:
        return next_weekday(s, from_date).strftime("%Y-%m-%d")
    # ISO date
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%Y-%m-%d")
    except Exception:
        raise ValueError(f"Invalid date string: {date_str}")

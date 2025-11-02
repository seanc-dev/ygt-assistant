"""Defer computation helper with hidden rules."""
from __future__ import annotations
from typing import Tuple, Optional
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from settings import DEFAULT_TZ


def compute_defer_until(
    bucket: str,
    now: datetime,
    user_settings: dict,
) -> Tuple[Optional[str], Optional[str]]:
    """Compute defer_until_iso and defer_bucket.
    
    Returns:
        (defer_until_iso, defer_bucket) or (None, None) if bucket should be hidden
    
    Hidden rules:
    - Hide 'afternoon' if now >= 16:00
    - Hide 'this_week' on Thu
    - On Fri, hide 'tomorrow' for this_week path (use next_week instead)
    """
    work_hours = user_settings.get("work_hours", {"start": "09:00", "end": "17:00"})
    time_zone = user_settings.get("time_zone", DEFAULT_TZ)
    
    try:
        tz = ZoneInfo(time_zone)
    except Exception:
        from datetime import timezone
        tz = timezone.utc
    
    # Ensure now is in correct timezone
    if now.tzinfo is None:
        now = now.replace(tzinfo=tz)
    else:
        now = now.astimezone(tz)
    
    def _is_workday(dt: datetime) -> bool:
        return dt.weekday() < 5
    
    def _next_workday(dt: datetime) -> datetime:
        days = 1
        while not _is_workday(dt + timedelta(days=days)):
            days += 1
        return dt + timedelta(days=days)
    
    def _parse_time(time_str: str) -> datetime:
        hour, minute = map(int, time_str.split(":"))
        return now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    start_time = _parse_time(work_hours["start"])
    end_time = _parse_time(work_hours["end"])
    
    if bucket == "afternoon":
        # Hide if now >= 16:00
        if now.hour >= 16:
            return (None, None)
        
        target = now.replace(hour=13, minute=0, second=0, microsecond=0)
        # If it's after work hours, move to next workday
        if now >= end_time:
            target = _next_workday(now).replace(hour=13, minute=0, second=0, microsecond=0)
        # If target is before now, move to next workday
        elif target < now:
            target = _next_workday(now).replace(hour=13, minute=0, second=0, microsecond=0)
        return (target.isoformat(), "afternoon")
    
    elif bucket == "tomorrow":
        target = _next_workday(now).replace(
            hour=int(work_hours["start"].split(":")[0]),
            minute=int(work_hours["start"].split(":")[1]),
            second=0,
            microsecond=0
        )
        return (target.isoformat(), "tomorrow")
    
    elif bucket == "this_week":
        # Hide on Thu
        if now.weekday() == 3:  # Thursday
            return (None, None)
        
        # If Wed -> Friday
        if now.weekday() == 2:  # Wednesday
            days_ahead = 2
            target = now + timedelta(days=days_ahead)
            target = target.replace(
                hour=int(work_hours["start"].split(":")[0]),
                minute=int(work_hours["start"].split(":")[1]),
                second=0,
                microsecond=0
            )
            return (target.isoformat(), "this_week")
        
        # If Fri -> hidden (should use next_week)
        if now.weekday() == 4:  # Friday
            return (None, None)
        
        # Otherwise, next available slot excluding tomorrow
        days_ahead = 2  # Skip tomorrow
        target = now + timedelta(days=days_ahead)
        # Ensure it's a workday
        while not _is_workday(target):
            target += timedelta(days=1)
        target = target.replace(
            hour=int(work_hours["start"].split(":")[0]),
            minute=int(work_hours["start"].split(":")[1]),
            second=0,
            microsecond=0
        )
        return (target.isoformat(), "this_week")
    
    elif bucket == "next_week":
        # Next Monday
        days_ahead = (7 - now.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7  # If it's Monday, go to next Monday
        target = now + timedelta(days=days_ahead)
        target = target.replace(
            hour=int(work_hours["start"].split(":")[0]),
            minute=int(work_hours["start"].split(":")[1]),
            second=0,
            microsecond=0
        )
        return (target.isoformat(), "next_week")
    
    else:
        raise ValueError(f"Unknown defer bucket: {bucket}")


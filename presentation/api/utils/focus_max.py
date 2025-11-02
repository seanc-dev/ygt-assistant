"""Calculate maximum focus block duration based on available time windows."""
from __future__ import annotations
from typing import Dict, Any
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


def calculate_focus_block_max(
    work_hours: Dict[str, str],
    day_shape: Dict[str, Any],
    default: int = 120,
) -> int:
    """Calculate maximum focus block duration.
    
    Takes into account:
    - Total work hours
    - Lunch window (subtracts max lunch duration)
    - Meeting avoid windows
    - Returns the largest possible continuous time window
    
    Defaults to 120 minutes if calculation fails.
    """
    try:
        # Parse work hours
        start_hour, start_min = map(int, work_hours["start"].split(":"))
        end_hour, end_min = map(int, work_hours["end"].split(":"))
        
        # Calculate total work minutes
        start_time = start_hour * 60 + start_min
        end_time = end_hour * 60 + end_min
        total_minutes = end_time - start_time
        
        # Subtract lunch window (use max_minutes)
        lunch_window = day_shape.get("lunch_window", {})
        lunch_max = lunch_window.get("max_minutes", 60)
        available_minutes = total_minutes - lunch_max
        
        # Consider meeting avoid windows
        meeting_avoid = day_shape.get("meeting_avoid_windows", [])
        for window in meeting_avoid:
            window_start_hour, window_start_min = map(int, window["start"].split(":"))
            window_end_hour, window_end_min = map(int, window["end"].split(":"))
            window_start = window_start_hour * 60 + window_start_min
            window_end = window_end_hour * 60 + window_end_min
            
            # Subtract avoid window from available time
            avoid_minutes = window_end - window_start
            available_minutes -= avoid_minutes
        
        # Calculate largest continuous window
        # Simplified: assume lunch splits day into two windows
        # Morning window: start to lunch start
        lunch_start_hour, lunch_start_min = map(int, lunch_window.get("start", "12:00").split(":"))
        lunch_start = lunch_start_hour * 60 + lunch_start_min
        morning_window = lunch_start - start_time
        
        # Afternoon window: lunch end to end
        lunch_end_hour, lunch_end_min = map(int, lunch_window.get("end", "14:00").split(":"))
        lunch_end = lunch_end_hour * 60 + lunch_end_min
        afternoon_window = end_time - lunch_end
        
        # Largest window is max of morning/afternoon (minus buffers)
        buffer_config = day_shape.get("buffer_minutes", {"min": 5, "max": 10})
        buffer_max = buffer_config.get("max") if isinstance(buffer_config, dict) else buffer_config
        
        max_window = max(morning_window, afternoon_window) - buffer_max
        
        # Ensure it's at least default (120) and reasonable (max 480 = 8 hours)
        calculated_max = max(default, min(max_window, 480))
        
        return calculated_max
    except Exception:
        # Fallback to default if calculation fails
        return default


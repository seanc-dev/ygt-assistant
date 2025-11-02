"""User settings repository (in-memory, interface for DB later)."""
from __future__ import annotations
from typing import Any, Dict, Optional
import re

# In-memory store: user_id -> settings
_settings_store: Dict[str, Dict[str, Any]] = {}


def _validate_time(time_str: str) -> bool:
    """Validate time string format HH:MM."""
    return bool(re.match(r"^([01]\d|2[0-3]):([0-5]\d)$", time_str))


def _validate_iana_tz(tz: str) -> bool:
    """Validate IANA timezone identifier."""
    try:
        from zoneinfo import ZoneInfo
        ZoneInfo(tz)
        return True
    except Exception:
        return False


def get_settings(user_id: str) -> Dict[str, Any]:
    """Get user settings with defaults."""
    if user_id not in _settings_store:
        return _default_settings()
    return _settings_store[user_id].copy()


def update_settings(user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """Update user settings with validation."""
    current = get_settings(user_id)
    
    # Validate and update work_hours
    if "work_hours" in updates:
        wh = updates["work_hours"]
        if not _validate_time(wh.get("start", "")):
            raise ValueError("Invalid work_hours.start format (expected HH:MM)")
        if not _validate_time(wh.get("end", "")):
            raise ValueError("Invalid work_hours.end format (expected HH:MM)")
        current["work_hours"] = wh
    
    # Validate and update time_zone
    if "time_zone" in updates:
        if not _validate_iana_tz(updates["time_zone"]):
            raise ValueError(f"Invalid IANA timezone: {updates['time_zone']}")
        current["time_zone"] = updates["time_zone"]
    
    # Update day_shape
    if "day_shape" in updates:
        ds = updates["day_shape"]
        # Validate day_shape fields
        if "morning_focus" in ds and not isinstance(ds["morning_focus"], bool):
            raise ValueError("day_shape.morning_focus must be boolean")
        if "focus_block_lengths_min" in ds:
            if not isinstance(ds["focus_block_lengths_min"], list):
                raise ValueError("day_shape.focus_block_lengths_min must be array")
        if "lunch_window" in ds:
            lw = ds["lunch_window"]
            if not _validate_time(lw.get("start", "")) or not _validate_time(lw.get("end", "")):
                raise ValueError("Invalid lunch_window format")
        if "meeting_avoid_windows" in ds:
            for window in ds["meeting_avoid_windows"]:
                if not _validate_time(window.get("start", "")) or not _validate_time(window.get("end", "")):
                    raise ValueError("Invalid meeting_avoid_windows format")
        if "buffer_minutes" in ds and not isinstance(ds["buffer_minutes"], int):
            raise ValueError("day_shape.buffer_minutes must be integer")
        current["day_shape"] = {**current.get("day_shape", {}), **ds}
    
    # Update translation
    if "translation" in updates:
        current["translation"] = updates["translation"]
    
    # Update trust_level
    if "trust_level" in updates:
        if updates["trust_level"] not in ["training-wheels", "standard", "autonomous"]:
            raise ValueError("Invalid trust_level")
        current["trust_level"] = updates["trust_level"]
    
    # Update ui_prefs
    if "ui_prefs" in updates:
        current["ui_prefs"] = {**current.get("ui_prefs", {}), **updates["ui_prefs"]}
    
    _settings_store[user_id] = current
    return current.copy()


def _default_settings() -> Dict[str, Any]:
    """Return default settings."""
    return {
        "work_hours": {
            "start": "09:00",
            "end": "17:00",
        },
        "time_zone": "UTC",
        "day_shape": {
            "morning_focus": True,
            "focus_block_lengths_min": [90, 60],
            "lunch_window": {
                "start": "12:00",
                "end": "14:00",
                "duration_min": 45,
            },
            "meeting_avoid_windows": [
                {"start": "16:00", "end": "17:00"},
            ],
            "buffer_minutes": 5,
        },
        "translation": {
            "enabled": False,
            "rules": {
                "outbound": False,
                "inbound": False,
                "internal": False,
                "external": False,
            },
        },
        "trust_level": "standard",
        "ui_prefs": {
            "thread_open_behavior": "new_tab",
            "brief": {
                "weather": False,
                "news": False,
                "tone": "professional",
            },
        },
    }


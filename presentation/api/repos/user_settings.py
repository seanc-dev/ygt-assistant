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
        if "focus_block_max_minutes" in ds:
            if not isinstance(ds["focus_block_max_minutes"], int) or ds["focus_block_max_minutes"] < 30:
                raise ValueError("day_shape.focus_block_max_minutes must be integer >= 30")
        if "lunch_window" in ds:
            lw = ds["lunch_window"]
            if not _validate_time(lw.get("start", "")) or not _validate_time(lw.get("end", "")):
                raise ValueError("Invalid lunch_window format")
            if "min_minutes" in lw and not isinstance(lw["min_minutes"], int):
                raise ValueError("lunch_window.min_minutes must be integer")
            if "max_minutes" in lw and not isinstance(lw["max_minutes"], int):
                raise ValueError("lunch_window.max_minutes must be integer")
        if "meeting_avoid_windows" in ds:
            for window in ds["meeting_avoid_windows"]:
                if not _validate_time(window.get("start", "")) or not _validate_time(window.get("end", "")):
                    raise ValueError("Invalid meeting_avoid_windows format")
        if "buffer_minutes" in ds:
            bm = ds["buffer_minutes"]
            if isinstance(bm, dict):
                if "min" in bm and not isinstance(bm["min"], int):
                    raise ValueError("day_shape.buffer_minutes.min must be integer")
                if "max" in bm and not isinstance(bm["max"], int):
                    raise ValueError("day_shape.buffer_minutes.max must be integer")
            elif not isinstance(bm, int):
                raise ValueError("day_shape.buffer_minutes must be integer or object with min/max")
        current["day_shape"] = {**current.get("day_shape", {}), **ds}
    
    # Update translation
    if "translation" in updates:
        trans = updates["translation"]
        if "default" in trans and trans["default"] not in ["llm", "azure"]:
            raise ValueError("translation.default must be 'llm' or 'azure'")
        if "fallback" in trans and trans["fallback"] not in ["llm", "azure"]:
            raise ValueError("translation.fallback must be 'llm' or 'azure'")
        if "rules" in trans:
            valid_rule_values = ["auto", "prompt", "off"]
            for key, value in trans["rules"].items():
                if value not in valid_rule_values:
                    raise ValueError(f"translation.rules.{key} must be one of: {valid_rule_values}")
        current["translation"] = {**current.get("translation", {}), **trans}
    
    # Update trust_level
    if "trust_level" in updates:
        if updates["trust_level"] not in ["training_wheels", "standard", "autonomous"]:
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
            "focus_block_max_minutes": 120,  # Default, will be calculated based on available time
            "lunch_window": {
                "start": "12:00",
                "end": "14:00",
                "min_minutes": 45,
                "max_minutes": 60,
            },
            "meeting_avoid_windows": [
                {"start": "16:00", "end": "23:59"},
            ],
            "buffer_minutes": {"min": 5, "max": 10},
        },
        "translation": {
            "default": "llm",
            "fallback": "azure",
            "rules": {
                "outbound": "auto",
                "inbound": "prompt",
                "internal": "off",
                "external": "auto",
            },
        },
        "trust_level": "training_wheels",
        "ui_prefs": {
            "thread_open_behavior": "new_tab",
            "brief": {
                "weather": False,
                "news": False,
                "tone": "neutral",
            },
            "hotkeys": {
                "approve": "a",
                "edit": "e",
                "defer": "d",
                "add_to_today": "t",
                "open_workroom": "o",
                "collapse": "Escape",
                "kanban_toggle": "Meta+k",
                "settings": "Meta+,",
            },
        },
    }


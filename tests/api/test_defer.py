"""Tests for defer computation."""
import pytest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from presentation.api.utils.defer import compute_defer_until
from settings import DEFAULT_TZ


def test_defer_afternoon_before_16():
    """Test afternoon defer before 16:00 returns today 13:00."""
    now = datetime.now(ZoneInfo(DEFAULT_TZ)).replace(hour=14, minute=0, second=0, microsecond=0)
    user_settings = {
        "work_hours": {"start": "09:00", "end": "17:00"},
        "time_zone": DEFAULT_TZ,
    }
    
    defer_until, bucket = compute_defer_until("afternoon", now, user_settings)
    
    assert defer_until is not None
    assert bucket == "afternoon"
    defer_dt = datetime.fromisoformat(defer_until)
    assert defer_dt.hour == 13
    assert defer_dt.minute == 0


def test_defer_afternoon_hidden_after_16():
    """Test afternoon defer is hidden after 16:00."""
    now = datetime.now(ZoneInfo(DEFAULT_TZ)).replace(hour=16, minute=30, second=0, microsecond=0)
    user_settings = {
        "work_hours": {"start": "09:00", "end": "17:00"},
        "time_zone": DEFAULT_TZ,
    }
    
    defer_until, bucket = compute_defer_until("afternoon", now, user_settings)
    
    assert defer_until is None
    assert bucket is None


def test_defer_this_week_hidden_on_thursday():
    """Test this_week defer is hidden on Thursday."""
    # Set to Thursday
    now = datetime.now(ZoneInfo(DEFAULT_TZ))
    days_until_thursday = (3 - now.weekday()) % 7
    if days_until_thursday == 0:
        days_until_thursday = 7
    thursday = now + timedelta(days=days_until_thursday)
    thursday = thursday.replace(hour=10, minute=0, second=0, microsecond=0)
    
    user_settings = {
        "work_hours": {"start": "09:00", "end": "17:00"},
        "time_zone": DEFAULT_TZ,
    }
    
    defer_until, bucket = compute_defer_until("this_week", thursday, user_settings)
    
    assert defer_until is None
    assert bucket is None


def test_defer_tomorrow_next_workday():
    """Test tomorrow defer returns next workday."""
    now = datetime.now(ZoneInfo(DEFAULT_TZ)).replace(hour=10, minute=0, second=0, microsecond=0)
    user_settings = {
        "work_hours": {"start": "09:00", "end": "17:00"},
        "time_zone": DEFAULT_TZ,
    }
    
    defer_until, bucket = compute_defer_until("tomorrow", now, user_settings)
    
    assert defer_until is not None
    assert bucket == "tomorrow"
    defer_dt = datetime.fromisoformat(defer_until)
    assert defer_dt.weekday() < 5  # Monday-Friday
    assert defer_dt.hour == 9
    assert defer_dt.minute == 0


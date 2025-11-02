"""Brief endpoint."""
from __future__ import annotations
from typing import Any, Dict
from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Request, Depends
from presentation.api.repos import user_settings
from presentation.api.routes.queue import _get_user_id
from settings import DEFAULT_TZ, FEATURE_WEATHER_NEWS

router = APIRouter()


@router.get("/api/brief/today")
async def brief_today(
    request: Request,
    user_id: str = Depends(_get_user_id),
) -> Dict[str, Any]:
    """Get today's brief with optional weather/news.
    
    Returns summary and optional weather/news if enabled.
    """
    user_settings_data = user_settings.get_settings(user_id)
    brief_prefs = user_settings_data.get("ui_prefs", {}).get("brief", {})
    time_zone = user_settings_data.get("time_zone", DEFAULT_TZ)
    
    try:
        tz = ZoneInfo(time_zone)
    except Exception:
        from datetime import timezone
        tz = timezone.utc
    
    now = datetime.now(tz)
    
    # Generate summary
    summary = f"Today is {now.strftime('%A, %B %d')}. "
    
    # Add weather if enabled
    weather = None
    if FEATURE_WEATHER_NEWS and brief_prefs.get("weather", False):
        # TODO: Integrate weather API (mock for now)
        weather = {
            "condition": "sunny",
            "temp": "72°F",
            "location": "San Francisco, CA",
        }
        summary += f"Weather: {weather['condition']}, {weather['temp']}. "
    
    # Add news if enabled
    news = None
    if FEATURE_WEATHER_NEWS and brief_prefs.get("news", False):
        # TODO: Integrate news API (mock for now)
        news = [
            {
                "title": "Tech industry updates",
                "summary": "Latest developments in AI and productivity tools",
                "source": "Tech News",
            }
        ]
        summary += f"Top news: {news[0]['title']}. "
    
    # Get tone from preferences
    tone = brief_prefs.get("tone", "professional")
    
    return {
        "ok": True,
        "date": now.date().isoformat(),
        "summary": summary.strip(),
        "weather": weather,
        "news": news,
        "tone": tone,
    }

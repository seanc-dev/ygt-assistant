"""Workload summary endpoint."""
from __future__ import annotations
from typing import Any, Dict, List
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Request, Depends
from presentation.api.repos import user_settings
from presentation.api.routes.queue import _get_user_id, queue_store
from presentation.api.routes.schedule import schedule_today
from presentation.api.stores import proposed_blocks_store
from settings import DEFAULT_TZ, _is_dev
import os

router = APIRouter()


def _calculate_planned_minutes_today(events: List[Dict[str, Any]], blocks: List[Dict[str, Any]]) -> int:
    """Calculate total planned minutes from events and blocks."""
    total_minutes = 0
    
    for event in events:
        try:
            start = datetime.fromisoformat(event.get("start", "").replace("Z", "+00:00"))
            end = datetime.fromisoformat(event.get("end", "").replace("Z", "+00:00"))
            delta = end - start
            total_minutes += int(delta.total_seconds() / 60)
        except Exception:
            continue
    
    for block in blocks:
        try:
            start = datetime.fromisoformat(block.get("start", "").replace("Z", "+00:00"))
            end = datetime.fromisoformat(block.get("end", "").replace("Z", "+00:00"))
            delta = end - start
            total_minutes += int(delta.total_seconds() / 60)
        except Exception:
            continue
    
    return total_minutes


def _get_active_minutes(blocks: List[Dict[str, Any]]) -> int:
    """Calculate active minutes from focus blocks that are in progress or started today.
    
    Only counts elapsed time, not future time. For blocks in progress, calculates
    the time elapsed from today_start (or block start if later) to now.
    For completed blocks that started today, counts full duration.
    """
    now = datetime.now(ZoneInfo("UTC"))
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    active_minutes = 0
    
    for block in blocks:
        try:
            start = datetime.fromisoformat(block.get("start", "").replace("Z", "+00:00"))
            end = datetime.fromisoformat(block.get("end", "").replace("Z", "+00:00"))
            
            # Only count blocks that started today or are currently in progress
            if start >= today_start:
                # Block started today
                if now >= end:
                    # Block completed: count full duration
                    delta = end - start
                    active_minutes += int(delta.total_seconds() / 60)
                elif now >= start:
                    # Block in progress: count elapsed time only
                    elapsed_start = max(start, today_start)
                    delta = now - elapsed_start
                    active_minutes += int(delta.total_seconds() / 60)
                # else: block hasn't started yet, count 0
            elif start <= now <= end:
                # Block started before today but is currently in progress: count elapsed time from today_start
                delta = now - today_start
                active_minutes += int(delta.total_seconds() / 60)
        except Exception:
            continue
    
    return active_minutes


def _get_today_items(
    events: List[Dict[str, Any]],
    blocks: List[Dict[str, Any]],
    queue_items: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Get today's focus items from schedule and queue."""
    items: List[Dict[str, Any]] = []
    
    # Add blocks from schedule
    for block in blocks:
        try:
            start = datetime.fromisoformat(block.get("start", "").replace("Z", "+00:00"))
            title = block.get("title", "Focus block")
            items.append({
                "id": block.get("id", ""),
                "title": title,
                "due": start.isoformat() if start else None,
                "source": "calendar",
                "priority": "med",  # Default for blocks
            })
        except Exception:
            continue
    
    # Add queue items marked as added_to_today
    for item in queue_items:
        if item.get("added_to_today"):
            priority_map = {
                "high": "high",
                "medium": "med",
                "low": "low",
            }
            items.append({
                "id": item.get("action_id", ""),
                "title": item.get("preview", "Action item")[:100],
                "due": item.get("defer_until"),
                "source": "queue",
                "priority": priority_map.get(item.get("priority", "medium"), "med"),
            })
    
    return items[:5]  # Limit to 5 items


def _get_weekly_stats(queue_items: List[Dict[str, Any]]) -> Dict[str, int]:
    """Calculate weekly triaged and completed stats."""
    now = datetime.now(ZoneInfo("UTC"))
    week_start = now - timedelta(days=7)
    
    triaged = 0
    completed = 0
    
    # Count items created in last 7 days as triaged
    for item in queue_items:
        created_at = item.get("created_at")
        if created_at:
            try:
                created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                if created >= week_start:
                    triaged += 1
            except Exception:
                continue
    
    # TODO: Track completed items when that feature is implemented
    # For now, use a placeholder
    completed = 0
    
    return {"triaged": triaged, "completed": completed}


@router.get("/api/workload/summary")
async def workload_summary(
    request: Request,
    user_id: str = Depends(_get_user_id),
) -> Dict[str, Any]:
    """Get workload summary with capacity, progress, and today's items.
    
    Returns:
    - plannedMin: Total planned minutes for today
    - activeMin: Focus blocks in progress or started today
    - overrunMin: Planned exceeded by actual (>=0)
    - today.items: Focus items for today (up to 5)
    - weekly: Weekly triaged and completed counts
    - rating: "manageable" | "rising" | "overloaded"
    """
    
    # DEV_MODE: Return deterministic mock data
    if _is_dev():
        return {
            "plannedMin": 420,  # 7 hours
            "activeMin": 180,  # 3 hours
            "overrunMin": 0,
            "today": {
                "items": [
                    {
                        "id": "mock-1",
                        "title": "Review Q4 planning doc",
                        "due": None,
                        "source": "queue",
                        "priority": "high",
                    },
                    {
                        "id": "mock-2",
                        "title": "Team standup",
                        "due": datetime.now().isoformat(),
                        "source": "calendar",
                        "priority": "med",
                    },
                    {
                        "id": "mock-3",
                        "title": "Finish sprint retrospective",
                        "due": None,
                        "source": "queue",
                        "priority": "med",
                    },
                ],
            },
            "weekly": {
                "triaged": 12,
                "completed": 9,
            },
            "rating": "manageable",
        }
    
    # Get today's schedule
    schedule_data = await schedule_today(request, user_id)
    events = schedule_data.get("events", [])
    blocks = schedule_data.get("blocks", [])
    
    # Calculate planned minutes
    planned_minutes = _calculate_planned_minutes_today(events, blocks)
    
    # Calculate active minutes
    active_minutes = _get_active_minutes(blocks)
    
    # Calculate overrun (planned exceeded by actual)
    overrun_minutes = max(0, active_minutes - planned_minutes)
    
    # Get queue items
    queue_items = list(queue_store.values())
    
    # Filter for user's queue items
    user_queue_items = [item for item in queue_items]
    
    # Get today's items
    today_items = _get_today_items(events, blocks, user_queue_items)
    
    # Get weekly stats
    weekly_stats = _get_weekly_stats(user_queue_items)
    
    # Calculate rating
    # Simple heuristic: manageable if planned < 8 hours, rising if 8-10 hours, overloaded if > 10 hours
    planned_hours = planned_minutes / 60
    if planned_hours < 8:
        rating = "manageable"
    elif planned_hours < 10:
        rating = "rising"
    else:
        rating = "overloaded"
    
    return {
        "plannedMin": planned_minutes,
        "activeMin": active_minutes,
        "overrunMin": overrun_minutes,
        "today": {
            "items": today_items,
        },
        "weekly": weekly_stats,
        "rating": rating,
    }


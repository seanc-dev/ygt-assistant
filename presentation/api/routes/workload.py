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


def _calculate_planned_minutes_today(
    events: List[Dict[str, Any]], blocks: List[Dict[str, Any]]
) -> int:
    """Calculate total planned minutes from events and blocks."""
    total_minutes = 0

    for event in events:
        try:
            start = datetime.fromisoformat(
                event.get("start", "").replace("Z", "+00:00")
            )
            end = datetime.fromisoformat(event.get("end", "").replace("Z", "+00:00"))
            delta = end - start
            total_minutes += int(delta.total_seconds() / 60)
        except Exception:
            continue

    for block in blocks:
        try:
            start = datetime.fromisoformat(
                block.get("start", "").replace("Z", "+00:00")
            )
            end = datetime.fromisoformat(block.get("end", "").replace("Z", "+00:00"))
            delta = end - start
            total_minutes += int(delta.total_seconds() / 60)
        except Exception:
            continue

    return total_minutes


def _get_triage_count_today(queue_items: List[Dict[str, Any]]) -> int:
    """Count Action Queue items due/flagged for triage today."""
    now = datetime.now(ZoneInfo("UTC"))
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    count = 0
    for item in queue_items:
        # Check if item is due today or flagged for triage
        defer_until = item.get("defer_until")
        if defer_until:
            try:
                defer_date = datetime.fromisoformat(defer_until.replace("Z", "+00:00"))
                if today_start <= defer_date < today_end:
                    count += 1
                    continue
            except Exception:
                pass

        # Check if item has no defer_until and is not archived (needs triage)
        if not defer_until and not item.get("archived"):
            count += 1

    return count


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
            start = datetime.fromisoformat(
                block.get("start", "").replace("Z", "+00:00")
            )
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
    queue_items: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Get today's focus items from schedule and queue."""
    items: List[Dict[str, Any]] = []

    # Add blocks from schedule
    for block in blocks:
        try:
            start = datetime.fromisoformat(
                block.get("start", "").replace("Z", "+00:00")
            )
            title = block.get("title", "Focus block")
            items.append(
                {
                    "id": block.get("id", ""),
                    "title": title,
                    "due": start.isoformat() if start else None,
                    "source": "calendar",
                    "priority": "med",  # Default for blocks
                }
            )
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
            items.append(
                {
                    "id": item.get("action_id", ""),
                    "title": item.get("preview", "Action item")[:100],
                    "due": item.get("defer_until"),
                    "source": "queue",
                    "priority": priority_map.get(item.get("priority", "medium"), "med"),
                }
            )

    return items[:5]  # Limit to 5 items


def _get_flow_week(queue_items: List[Dict[str, Any]]) -> Dict[str, int]:
    """Calculate weekly action lifecycle counts.

    Returns counts for:
    - deferred: Items deferred to later dates
    - scheduled: Items assigned a specific time window
    - planned: Items committed to upcoming capacity
    - completed: Items done and archived
    """
    now = datetime.now(ZoneInfo("UTC"))
    week_start = now - timedelta(days=7)

    deferred = 0
    scheduled = 0
    planned = 0
    completed = 0

    for item in queue_items:
        # Check if item was created/modified in last 7 days
        created_at = item.get("created_at")
        modified_at = item.get("modified_at") or created_at

        if not modified_at:
            continue

        try:
            modified = datetime.fromisoformat(modified_at.replace("Z", "+00:00"))
            if modified < week_start:
                continue
        except Exception:
            continue

        # Categorize by status/bucket (mutually exclusive)
        # IMPORTANT: Use elif chain to prevent double-counting. Each item
        # should be counted in exactly one category based on priority:
        # 1. Completed (archived) takes precedence
        # 2. Scheduled (added_to_today or scheduled_at) next
        # 3. Planned (explicitly planned) next
        # 4. Deferred (defer_until set) last
        # Items without any of these statuses are not counted
        if item.get("archived"):
            completed += 1
        elif item.get("added_to_today") or item.get("scheduled_at"):
            scheduled += 1
        elif item.get("planned"):
            planned += 1
        elif item.get("defer_until"):
            deferred += 1
        # Items without explicit status are not counted in any category

    return {
        "deferred": deferred,
        "scheduled": scheduled,
        "planned": planned,
        "completed": completed,
        "total": deferred + scheduled + planned + completed,
    }


@router.get("/api/workload/summary")
async def workload_summary(
    request: Request,
    user_id: str = Depends(_get_user_id),
) -> Dict[str, Any]:
    """Get workload summary with capacity, progress, and today's items.

    Returns:
    - capacityMin: User-configured daily capacity (default 480 = 8 hours)
    - plannedMin: Total planned minutes for today
    - focusedMin: Focus blocks logged/started today
    - overbookedMin: plannedMin - capacityMin, clamped >=0
    - triageCountToday: Action Queue items due/flagged for triage today
    - today.items: Focus items for today (up to 5)
    - weekly: Weekly triaged and completed counts
    - rating: "manageable" | "rising" | "overloaded"
    """

    # Default capacity: 8 hours (480 minutes)
    capacity_min = 480

    # DEV_MODE: Return deterministic mock data
    if _is_dev():
        return {
            "capacityMin": 480,
            "plannedMin": 420,  # 7 hours
            "focusedMin": 180,  # 3 hours
            "overbookedMin": 0,
            "triageCountToday": 6,
            "today": {
                "focus": [
                    {
                        "id": "mock-1",
                        "title": "Review Q4 planning doc",
                        "source": "task",
                        "urgent": True,
                    },
                    {
                        "id": "mock-2",
                        "title": "Team standup",
                        "source": "calendar",
                    },
                    {
                        "id": "mock-3",
                        "title": "Finish sprint retrospective",
                        "source": "ai",
                    },
                ],
            },
            "flowWeek": {
                "deferred": 3,
                "scheduled": 5,
                "planned": 4,
                "completed": 9,
                "total": 21,
            },
            "lastSyncIso": datetime.now().isoformat(),
            "rating": "manageable",
        }

    # Get today's schedule
    schedule_data = await schedule_today(request, user_id)
    events = schedule_data.get("events", [])
    blocks = schedule_data.get("blocks", [])

    # Calculate planned minutes
    planned_minutes = _calculate_planned_minutes_today(events, blocks)

    # Calculate focused minutes (renamed from active)
    focused_minutes = _get_active_minutes(blocks)

    # Calculate overbooked (planned exceeded capacity)
    overbooked_minutes = max(0, planned_minutes - capacity_min)

    # Get queue items
    queue_items = list(queue_store.values())

    # Filter for user's queue items
    user_queue_items = [item for item in queue_items]

    # Get triage count for today
    triage_count = _get_triage_count_today(user_queue_items)

    # Get today's items (map to new structure)
    today_items_raw = _get_today_items(events, blocks, user_queue_items)
    today_focus = [
        {
            "id": item.get("id", ""),
            "title": item.get("title", ""),
            "source": "calendar" if item.get("source") == "calendar" else "task",
            "urgent": item.get("priority") == "high",
        }
        for item in today_items_raw
    ]

    # Get flow week stats
    flow_week = _get_flow_week(user_queue_items)

    # Calculate rating based on utilization and overbooked
    utilization_pct = planned_minutes / capacity_min if capacity_min > 0 else 0
    if overbooked_minutes > 0 or utilization_pct > 0.95:
        rating = "overloaded"
    elif utilization_pct >= 0.75:
        rating = "rising"
    else:
        rating = "manageable"

    return {
        "capacityMin": capacity_min,
        "plannedMin": planned_minutes,
        "focusedMin": focused_minutes,
        "overbookedMin": overbooked_minutes,
        "today": {
            "focus": today_focus,
        },
        "flowWeek": flow_week,
        "lastSyncIso": datetime.now().isoformat(),
        "rating": rating,
    }

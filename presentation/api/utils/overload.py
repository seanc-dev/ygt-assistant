"""Overload detection and proposal generation."""

from __future__ import annotations
from typing import Any, Dict, List
from datetime import datetime
from zoneinfo import ZoneInfo


def detect_overload(
    existing_events: List[Dict[str, Any]],
    proposed_blocks: List[Dict[str, Any]],
    user_settings: Dict[str, Any],
    fixed_personal_blocks: List[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Detect overload and generate proposals.

    Priority order (highest first):
    1. External meetings
    2. Internal meetings
    3. Deadlined tasks
    4. Focus work
    5. Admin

    Overload thresholds:
    - ≤30 min: squeeze using buffers and trim admin blocks first
    - 30–120 min: propose reschedule lower-priority items
    - >120 min: propose reschedule + offer declines for optional items

    Decline candidates:
    - Optional FYI meetings without external attendees
    - Duplicate stand-ups
    - Non-critical admin blocks

    Reschedule rules:
    - Internal meetings first, to next free window in same week; keep participants intact
    - Admin/focus tasks next; move to "tomorrow/this_week/next_week" per defer rules
    """
    work_hours = user_settings.get("work_hours", {"start": "09:00", "end": "17:00"})
    day_shape = user_settings.get("day_shape", {})
    buffer_config = day_shape.get("buffer_minutes", {"min": 5, "max": 10})
    buffer_min = (
        buffer_config.get("min") if isinstance(buffer_config, dict) else buffer_config
    )
    buffer_max = (
        buffer_config.get("max") if isinstance(buffer_config, dict) else buffer_config
    )

    # Calculate available minutes
    time_zone = user_settings.get("time_zone", "UTC")
    try:
        tz = ZoneInfo(time_zone)
    except Exception:
        from datetime import timezone

        tz = timezone.utc

    now = datetime.now(tz)
    today_start = now.replace(
        hour=int(work_hours["start"].split(":")[0]),
        minute=int(work_hours["start"].split(":")[1]),
        second=0,
        microsecond=0,
    )
    today_end = now.replace(
        hour=int(work_hours["end"].split(":")[0]),
        minute=int(work_hours["end"].split(":")[1]),
        second=0,
        microsecond=0,
    )

    total_minutes = int((today_end - today_start).total_seconds() / 60)

    # Existing events minutes
    existing_minutes = sum(
        int(
            (
                datetime.fromisoformat(e["end"].replace("Z", "+00:00"))
                - datetime.fromisoformat(e["start"].replace("Z", "+00:00"))
            ).total_seconds()
            / 60
        )
        for e in existing_events
    )

    # Fixed personal blocks minutes
    fixed_minutes = sum(
        int(
            (
                datetime.fromisoformat(b["end"].replace("Z", "+00:00"))
                - datetime.fromisoformat(b["start"].replace("Z", "+00:00"))
            ).total_seconds()
            / 60
        )
        for b in (fixed_personal_blocks or [])
    )

    # Required buffers (use max for worst case)
    buffer_total = len(proposed_blocks) * buffer_max

    available_minutes = total_minutes - existing_minutes - fixed_minutes - buffer_total

    # Estimate proposed block minutes
    proposed_minutes = sum(b.get("estimated_minutes", 60) for b in proposed_blocks)

    overload_amount = proposed_minutes - available_minutes
    overload_detected = overload_amount > 0

    proposals = []

    if overload_detected:
        # Sort blocks by priority
        priority_order = {
            "external_meeting": 1,
            "internal_meeting": 2,
            "deadlined_task": 3,
            "focus": 4,
            "admin": 5,
        }

        sorted_blocks = sorted(
            proposed_blocks,
            key=lambda b: priority_order.get(
                b.get("kind", "admin"), priority_order.get(b.get("priority", "low"), 5)
            ),
        )

        if overload_amount <= 30:
            # Squeeze: trim admin blocks first, reduce buffers
            admin_blocks = [b for b in sorted_blocks if b.get("kind") == "admin"]
            for block in admin_blocks[:2]:  # Trim up to 2 admin blocks
                proposals.append(
                    {
                        "type": "trim",
                        "target_id": block.get("id", ""),
                        "reason": "Squeeze schedule by trimming admin blocks",
                        "requires_approval": False,
                    }
                )

        elif overload_amount <= 120:
            # Reschedule lower-priority items
            low_priority = sorted_blocks[-3:]  # Last 3 (lowest priority)
            for block in low_priority:
                if block.get("kind") in ["admin", "focus"]:
                    proposals.append(
                        {
                            "type": "reschedule",
                            "target_id": block.get("id", ""),
                            "reason": f"Reschedule to next available window",
                            "requires_approval": True,
                        }
                    )
                elif block.get("kind") == "internal_meeting":
                    proposals.append(
                        {
                            "type": "reschedule",
                            "target_id": block.get("id", ""),
                            "reason": "Reschedule internal meeting to next free window this week",
                            "requires_approval": True,
                        }
                    )

        else:
            # >120 min: reschedule + decline optional items
            # Decline candidates
            decline_candidates = [
                b
                for b in sorted_blocks
                if (
                    b.get("kind") == "fyi_meeting"
                    or (b.get("kind") == "admin" and not b.get("critical", False))
                    or b.get("duplicate_standup", False)
                )
            ]

            for block in decline_candidates[:2]:  # Up to 2 declines
                proposals.append(
                    {
                        "type": "decline",
                        "target_id": block.get("id", ""),
                        "reason": "Optional item; insufficient time available",
                        "requires_approval": True,
                    }
                )

            # Reschedule remaining
            reschedule_blocks = [
                b
                for b in sorted_blocks
                if b.get("id") not in [c.get("id") for c in decline_candidates[:2]]
            ][
                -3:
            ]  # Last 3 after declines

            for block in reschedule_blocks:
                if block.get("kind") == "internal_meeting":
                    proposals.append(
                        {
                            "type": "reschedule",
                            "target_id": block.get("id", ""),
                            "reason": "Reschedule to next free window this week",
                            "requires_approval": True,
                        }
                    )
                else:
                    proposals.append(
                        {
                            "type": "reschedule",
                            "target_id": block.get("id", ""),
                            "reason": "Reschedule to tomorrow/this_week/next_week",
                            "requires_approval": True,
                        }
                    )

    return {
        "detected": overload_detected,
        "available_minutes": available_minutes,
        "proposed_minutes": proposed_minutes,
        "overload_amount": overload_amount,
        "proposals": proposals,
    }

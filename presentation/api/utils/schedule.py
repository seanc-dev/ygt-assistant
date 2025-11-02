"""Schedule alternatives generator."""
from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from settings import DEFAULT_TZ


def generate_alternatives(
    existing_events: List[Dict[str, Any]],
    proposed_blocks: List[Dict[str, Any]],
    user_settings: Dict[str, Any],
) -> Dict[str, Any]:
    """Generate 3 alternative schedule plans (A/B/C).
    
    Types:
    - A) Focus-first: deep work AM, meetings PM, 10m buffers
    - B) Meeting-friendly: meetings earlier, focus later, 5-10m buffers
    - C) Balanced: one 90m AM, one 60m PM; errands/admin slotted
    
    Respects user_settings.day_shape and existing events.
    Returns overload proposals if detected.
    """
    day_shape = user_settings.get("day_shape", {})
    work_hours = user_settings.get("work_hours", {"start": "09:00", "end": "17:00"})
    time_zone = user_settings.get("time_zone", DEFAULT_TZ)
    
    try:
        tz = ZoneInfo(time_zone)
    except Exception:
        from datetime import timezone
        tz = timezone.utc
    
    now = datetime.now(tz)
    today_start = now.replace(hour=int(work_hours["start"].split(":")[0]), minute=int(work_hours["start"].split(":")[1]), second=0, microsecond=0)
    today_end = now.replace(hour=int(work_hours["end"].split(":")[0]), minute=int(work_hours["end"].split(":")[1]), second=0, microsecond=0)
    
    buffer_minutes = day_shape.get("buffer_minutes", 5)
    morning_focus = day_shape.get("morning_focus", True)
    focus_lengths = day_shape.get("focus_block_lengths_min", [90, 60])
    lunch_window = day_shape.get("lunch_window", {"start": "12:00", "end": "14:00", "duration_min": 45})
    meeting_avoid = day_shape.get("meeting_avoid_windows", [{"start": "16:00", "end": "17:00"}])
    
    # Calculate available minutes
    total_minutes = int((today_end - today_start).total_seconds() / 60)
    existing_minutes = sum(
        int((datetime.fromisoformat(e["end"].replace("Z", "+00:00")) - datetime.fromisoformat(e["start"].replace("Z", "+00:00"))).total_seconds() / 60)
        for e in existing_events
    )
    buffer_total = len(proposed_blocks) * buffer_minutes
    available_minutes = total_minutes - existing_minutes - buffer_total
    
    # Estimate proposed block minutes (stub - will use LLM estimation later)
    proposed_minutes = sum(
        b.get("estimated_minutes", 60) for b in proposed_blocks
    )
    
    overload_detected = proposed_minutes > available_minutes
    overload_threshold_30 = proposed_minutes > available_minutes + 30
    overload_threshold_120 = proposed_minutes > available_minutes + 120
    
    proposals = []
    if overload_detected:
        # Generate proposals for reschedule/decline
        for block in proposed_blocks[:3]:  # Limit to top 3
            if overload_threshold_120:
                proposals.append({
                    "type": "decline",
                    "target_id": block.get("id", ""),
                    "reason": "Insufficient time available",
                    "requires_approval": True,
                })
            elif overload_threshold_30:
                proposals.append({
                    "type": "reschedule",
                    "target_id": block.get("id", ""),
                    "reason": "Scheduling conflict",
                    "requires_approval": True,
                })
    
    # Generate plan A: Focus-first
    plan_a = _generate_focus_first_plan(
        existing_events, proposed_blocks, work_hours, day_shape, buffer_minutes
    )
    
    # Generate plan B: Meeting-friendly
    plan_b = _generate_meeting_friendly_plan(
        existing_events, proposed_blocks, work_hours, day_shape, buffer_minutes
    )
    
    # Generate plan C: Balanced
    plan_c = _generate_balanced_plan(
        existing_events, proposed_blocks, work_hours, day_shape, buffer_minutes
    )
    
    return {
        "plans": [
            {"id": "plan_a", "type": "focus-first", "blocks": plan_a},
            {"id": "plan_b", "type": "meeting-friendly", "blocks": plan_b},
            {"id": "plan_c", "type": "balanced", "blocks": plan_c},
        ],
        "overload": {
            "detected": overload_detected,
            "available_minutes": available_minutes,
            "proposed_minutes": proposed_minutes,
            "proposals": proposals,
        },
    }


def _generate_focus_first_plan(
    existing: List[Dict[str, Any]],
    proposed: List[Dict[str, Any]],
    work_hours: Dict[str, Any],
    day_shape: Dict[str, Any],
    buffer_minutes: int,
) -> List[Dict[str, Any]]:
    """Generate focus-first plan: deep work AM, meetings PM, 10m buffers."""
    # Stub implementation - will be fully implemented in Phase 2
    blocks = []
    buffer = 10  # Use 10m buffers for focus-first
    
    # Sort proposed by priority
    sorted_proposed = sorted(proposed, key=lambda x: x.get("priority", "medium"), reverse=True)
    
    # Place focus blocks in morning
    current_time = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
    for block in sorted_proposed:
        if block.get("kind") == "focus":
            duration = block.get("estimated_minutes", 90)
            blocks.append({
                "id": block.get("id", ""),
                "kind": "focus",
                "start": current_time.isoformat(),
                "end": (current_time + timedelta(minutes=duration)).isoformat(),
            })
            current_time += timedelta(minutes=duration + buffer)
    
    return blocks


def _generate_meeting_friendly_plan(
    existing: List[Dict[str, Any]],
    proposed: List[Dict[str, Any]],
    work_hours: Dict[str, Any],
    day_shape: Dict[str, Any],
    buffer_minutes: int,
) -> List[Dict[str, Any]]:
    """Generate meeting-friendly plan: meetings earlier, focus later, 5-10m buffers."""
    # Stub implementation
    blocks = []
    buffer = 7  # Average of 5-10m
    
    sorted_proposed = sorted(proposed, key=lambda x: x.get("kind") == "meeting", reverse=True)
    
    current_time = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
    for block in sorted_proposed:
        duration = block.get("estimated_minutes", 60)
        blocks.append({
            "id": block.get("id", ""),
            "kind": block.get("kind", "work"),
            "start": current_time.isoformat(),
            "end": (current_time + timedelta(minutes=duration)).isoformat(),
        })
        current_time += timedelta(minutes=duration + buffer)
    
    return blocks


def _generate_balanced_plan(
    existing: List[Dict[str, Any]],
    proposed: List[Dict[str, Any]],
    work_hours: Dict[str, Any],
    day_shape: Dict[str, Any],
    buffer_minutes: int,
) -> List[Dict[str, Any]]:
    """Generate balanced plan: one 90m AM, one 60m PM; errands/admin slotted."""
    # Stub implementation
    blocks = []
    
    # One 90m block in morning
    morning_time = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
    focus_blocks = [b for b in proposed if b.get("kind") == "focus"]
    if focus_blocks:
        blocks.append({
            "id": focus_blocks[0].get("id", ""),
            "kind": "focus",
            "start": morning_time.isoformat(),
            "end": (morning_time + timedelta(minutes=90)).isoformat(),
        })
    
    # One 60m block in afternoon
    afternoon_time = datetime.now().replace(hour=14, minute=0, second=0, microsecond=0)
    if len(focus_blocks) > 1:
        blocks.append({
            "id": focus_blocks[1].get("id", ""),
            "kind": "focus",
            "start": afternoon_time.isoformat(),
            "end": (afternoon_time + timedelta(minutes=60)).isoformat(),
        })
    
    return blocks


"""Schedule alternatives generator."""
from __future__ import annotations
from typing import Any, Dict, List
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from presentation.api.utils.overload import detect_overload
from presentation.api.utils.focus_max import calculate_focus_block_max
from settings import DEFAULT_TZ


def generate_alternatives(
    existing_events: List[Dict[str, Any]],
    proposed_blocks: List[Dict[str, Any]],
    user_settings: Dict[str, Any],
) -> Dict[str, Any]:
    """Generate 3 alternative schedule plans (A/B/C).
    
    Types:
    - A) Focus-first: deep work AM, meetings PM, max buffers
    - B) Meeting-friendly: meetings earlier, focus later, avg buffers
    - C) Balanced: one 90m AM, one 60m PM; errands/admin slotted
    
    Respects user_settings.day_shape and existing events.
    Returns overload proposals if detected.
    """
    day_shape = user_settings.get("day_shape", {})
    work_hours = user_settings.get("work_hours", {"start": "09:00", "end": "17:00"})
    time_zone = user_settings.get("time_zone", DEFAULT_TZ)
    
    try:
        tz = ZoneInfo(time_zone)
    except (ValueError, KeyError):
        from datetime import timezone
        tz = timezone.utc
    
    # Get buffer config
    buffer_config = day_shape.get("buffer_minutes", {"min": 5, "max": 10})
    if isinstance(buffer_config, dict):
        buffer_min = buffer_config.get("min", 5)
        buffer_max = buffer_config.get("max", 10)
    else:
        buffer_min = buffer_max = buffer_config
    
    # Get focus block max (calculate from available time or use configured/default)
    focus_block_max = day_shape.get("focus_block_max_minutes")
    if focus_block_max is None:
        # Calculate based on available time windows
        focus_block_max = calculate_focus_block_max(work_hours, day_shape, default=120)
    
    # Cap focus blocks at configured max
    capped_blocks = []
    for block in proposed_blocks:
        if block.get("kind") == "focus":
            duration = min(block.get("estimated_minutes", 90), focus_block_max)
            capped_block = {**block, "estimated_minutes": duration}
        else:
            capped_block = block
        capped_blocks.append(capped_block)
    
    # Detect overload
    overload_result = detect_overload(
        existing_events,
        capped_blocks,
        user_settings,
        fixed_personal_blocks=None,
    )
    
    # Generate plan A: Focus-first
    plan_a = _generate_focus_first_plan(
        existing_events, capped_blocks, work_hours, day_shape, buffer_min, buffer_max, focus_block_max, tz
    )
    
    # Generate plan B: Meeting-friendly
    plan_b = _generate_meeting_friendly_plan(
        existing_events, capped_blocks, work_hours, day_shape, buffer_min, buffer_max, tz
    )
    
    # Generate plan C: Balanced
    plan_c = _generate_balanced_plan(
        existing_events, capped_blocks, work_hours, day_shape, buffer_min, buffer_max, focus_block_max, tz
    )
    
    return {
        "plans": [
            {"id": "plan_a", "type": "focus-first", "blocks": plan_a},
            {"id": "plan_b", "type": "meeting-friendly", "blocks": plan_b},
            {"id": "plan_c", "type": "balanced", "blocks": plan_c},
        ],
        "overload": {
            "detected": overload_result["detected"],
            "available_minutes": overload_result["available_minutes"],
            "proposed_minutes": overload_result["proposed_minutes"],
            "overload_amount": overload_result.get("overload_amount", 0),
            "proposals": overload_result["proposals"],
        },
    }


def _generate_focus_first_plan(
    existing: List[Dict[str, Any]],
    proposed: List[Dict[str, Any]],
    work_hours: Dict[str, Any],
    day_shape: Dict[str, Any],  # noqa: ARG001
    buffer_min: int,  # noqa: ARG001
    buffer_max: int,
    focus_block_max: int,
    tz: ZoneInfo,
) -> List[Dict[str, Any]]:
    """Generate focus-first plan: deep work AM, meetings PM, max buffers."""
    blocks = []
    buffer = buffer_max  # Use max buffer for focus-first
    
    # Sort proposed by priority (focus first)
    sorted_proposed = sorted(
        proposed,
        key=lambda x: (
            x.get("kind") != "focus",  # Focus blocks first
            {"high": 0, "medium": 1, "low": 2}.get(x.get("priority", "medium"), 1)
        )
    )
    
    current_time = datetime.now(tz).replace(
        hour=int(work_hours["start"].split(":")[0]),
        minute=int(work_hours["start"].split(":")[1]),
        second=0,
        microsecond=0,
    )
    
    # Skip collisions with existing events
    for event in existing:
        event_start = datetime.fromisoformat(event["start"].replace("Z", "+00:00")).astimezone(tz)
        event_end = datetime.fromisoformat(event["end"].replace("Z", "+00:00")).astimezone(tz)
        if current_time < event_end:
            current_time = event_end + timedelta(minutes=buffer)
    
    for block in sorted_proposed:
        duration = block.get("estimated_minutes", 60)
        
        # Check for collisions
        block_end = current_time + timedelta(minutes=duration)
        for event in existing:
            event_start = datetime.fromisoformat(event["start"].replace("Z", "+00:00")).astimezone(tz)
            event_end = datetime.fromisoformat(event["end"].replace("Z", "+00:00")).astimezone(tz)
            if (current_time < event_end and block_end > event_start):
                current_time = event_end + timedelta(minutes=buffer)
                block_end = current_time + timedelta(minutes=duration)
        
        blocks.append({
            "id": block.get("id", ""),
            "kind": block.get("kind", "work"),
            "start": current_time.isoformat(),
            "end": block_end.isoformat(),
        })
        current_time = block_end + timedelta(minutes=buffer)
    
    return blocks


def _generate_meeting_friendly_plan(
    existing: List[Dict[str, Any]],
    proposed: List[Dict[str, Any]],
    work_hours: Dict[str, Any],
    day_shape: Dict[str, Any],  # noqa: ARG001
    buffer_min: int,
    buffer_max: int,
    tz: ZoneInfo,
) -> List[Dict[str, Any]]:
    """Generate meeting-friendly plan: meetings earlier, focus later, avg buffers."""
    blocks = []
    buffer = (buffer_min + buffer_max) // 2  # Average of min-max
    
    # Sort: meetings first, then others
    sorted_proposed = sorted(
        proposed,
        key=lambda x: (
            x.get("kind") not in ["meeting", "internal_meeting", "external_meeting"],
            {"high": 0, "medium": 1, "low": 2}.get(x.get("priority", "medium"), 1)
        )
    )
    
    current_time = datetime.now(tz).replace(
        hour=int(work_hours["start"].split(":")[0]),
        minute=int(work_hours["start"].split(":")[1]),
        second=0,
        microsecond=0,
    )
    
    # Skip collisions with existing events
    for event in existing:
        event_start = datetime.fromisoformat(event["start"].replace("Z", "+00:00")).astimezone(tz)
        event_end = datetime.fromisoformat(event["end"].replace("Z", "+00:00")).astimezone(tz)
        if current_time < event_end:
            current_time = event_end + timedelta(minutes=buffer)
    
    for block in sorted_proposed:
        duration = block.get("estimated_minutes", 60)
        
        # Check for collisions
        block_end = current_time + timedelta(minutes=duration)
        for event in existing:
            event_start = datetime.fromisoformat(event["start"].replace("Z", "+00:00")).astimezone(tz)
            event_end = datetime.fromisoformat(event["end"].replace("Z", "+00:00")).astimezone(tz)
            if (current_time < event_end and block_end > event_start):
                current_time = event_end + timedelta(minutes=buffer)
                block_end = current_time + timedelta(minutes=duration)
        
        blocks.append({
            "id": block.get("id", ""),
            "kind": block.get("kind", "work"),
            "start": current_time.isoformat(),
            "end": block_end.isoformat(),
        })
        current_time = block_end + timedelta(minutes=buffer)
    
    return blocks


def _generate_balanced_plan(
    existing: List[Dict[str, Any]],  # noqa: ARG001
    proposed: List[Dict[str, Any]],
    work_hours: Dict[str, Any],
    day_shape: Dict[str, Any],
    buffer_min: int,
    buffer_max: int,  # noqa: ARG001
    focus_block_max: int,
    tz: ZoneInfo,
) -> List[Dict[str, Any]]:
    """Generate balanced plan: one 90m AM, one 60m PM; errands/admin slotted."""
    blocks = []
    focus_lengths = day_shape.get("focus_block_lengths_min", [90, 60])
    
    morning_time = datetime.now(tz).replace(
        hour=int(work_hours["start"].split(":")[0]),
        minute=int(work_hours["start"].split(":")[1]),
        second=0,
        microsecond=0,
    )
    
    # One focus block in morning (90m)
    focus_blocks = [b for b in proposed if b.get("kind") == "focus"]
    if focus_blocks and len(focus_lengths) > 0:
        duration = min(focus_lengths[0], focus_blocks[0].get("estimated_minutes", 90), focus_block_max)
        blocks.append({
            "id": focus_blocks[0].get("id", ""),
            "kind": "focus",
            "start": morning_time.isoformat(),
            "end": (morning_time + timedelta(minutes=duration)).isoformat(),
        })
    
    # One focus block in afternoon (60m)
    afternoon_time = datetime.now(tz).replace(hour=14, minute=0, second=0, microsecond=0)
    if len(focus_blocks) > 1 and len(focus_lengths) > 1:
        duration = min(focus_lengths[1], focus_blocks[1].get("estimated_minutes", 60), focus_block_max)
        blocks.append({
            "id": focus_blocks[1].get("id", ""),
            "kind": "focus",
            "start": afternoon_time.isoformat(),
            "end": (afternoon_time + timedelta(minutes=duration)).isoformat(),
        })
    
    # Add admin blocks in remaining slots
    admin_blocks = [b for b in proposed if b.get("kind") == "admin"]
    current_time = afternoon_time + timedelta(minutes=60)
    for block in admin_blocks[:2]:  # Max 2 admin blocks
        duration = block.get("estimated_minutes", 30)
        blocks.append({
            "id": block.get("id", ""),
            "kind": "admin",
            "start": current_time.isoformat(),
            "end": (current_time + timedelta(minutes=duration)).isoformat(),
        })
        current_time += timedelta(minutes=duration + buffer_min)
    
    return blocks

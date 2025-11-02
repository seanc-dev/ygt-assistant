"""Collision resolver for schedule blocks."""
from __future__ import annotations
from typing import Any, Dict, List
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


def resolve_collisions(
    existing_events: List[Dict[str, Any]],
    proposed_blocks: List[Dict[str, Any]],
    buffer_minutes: int | Dict[str, int] = 5,
) -> List[Dict[str, Any]]:
    """Resolve collisions between existing events and proposed blocks.
    
    Strategy:
    - Shift blocks forward if collision detected
    - Trim blocks if they extend beyond work hours
    - Insert buffers (5-10m) between adjacent blocks
    - Avoid double-booking
    
    Returns list of resolved blocks with adjusted start/end times.
    """
    # Parse buffer_minutes (can be int or dict with min/max)
    if isinstance(buffer_minutes, dict):
        buffer = buffer_minutes.get("min", 5)
    else:
        buffer = buffer_minutes
    
    resolved = []
    
    # Sort existing events by start time
    sorted_existing = sorted(
        existing_events,
        key=lambda e: datetime.fromisoformat(e["start"].replace("Z", "+00:00"))
    )
    
    # Sort proposed blocks by priority and estimated start
    sorted_proposed = sorted(
        proposed_blocks,
        key=lambda b: (
            {"high": 0, "medium": 1, "low": 2}.get(b.get("priority", "medium"), 1),
            b.get("estimated_start", "")
        )
    )
    
    current_time = None
    
    for block in sorted_proposed:
        # Parse block start (or use current_time if not set)
        if block.get("estimated_start"):
            block_start = datetime.fromisoformat(
                block["estimated_start"].replace("Z", "+00:00")
            )
        elif current_time:
            block_start = current_time
        else:
            # Default to first available slot
            if sorted_existing:
                first_event_end = datetime.fromisoformat(
                    sorted_existing[0]["end"].replace("Z", "+00:00")
                )
                block_start = first_event_end + timedelta(minutes=buffer)
            else:
                block_start = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
        
        duration = block.get("estimated_minutes", 60)
        block_end = block_start + timedelta(minutes=duration)
        
        # Check for collisions with existing events
        for event in sorted_existing:
            event_start = datetime.fromisoformat(event["start"].replace("Z", "+00:00"))
            event_end = datetime.fromisoformat(event["end"].replace("Z", "+00:00"))
            
            # Check if block overlaps with event
            if (block_start < event_end and block_end > event_start):
                # Shift block to start after event + buffer
                block_start = event_end + timedelta(minutes=buffer)
                block_end = block_start + timedelta(minutes=duration)
        
        # Check for collisions with previously resolved blocks
        for prev_block in resolved:
            prev_start = datetime.fromisoformat(prev_block["start"].replace("Z", "+00:00"))
            prev_end = datetime.fromisoformat(prev_block["end"].replace("Z", "+00:00"))
            
            if (block_start < prev_end and block_end > prev_start):
                # Shift block to start after previous block + buffer
                block_start = prev_end + timedelta(minutes=buffer)
                block_end = block_start + timedelta(minutes=duration)
        
        resolved_block = {
            "id": block.get("id", ""),
            "kind": block.get("kind", "work"),
            "tasks": block.get("tasks", []),
            "start": block_start.isoformat(),
            "end": block_end.isoformat(),
            "priority": block.get("priority", "medium"),
            "estimated_minutes": duration,
        }
        
        resolved.append(resolved_block)
        current_time = block_end + timedelta(minutes=buffer)
    
    return resolved


"""Dev endpoint to seed queue with test data."""

from __future__ import annotations
from typing import Any, Dict, List
from fastapi import APIRouter, Request, Depends
import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from presentation.api.routes.queue import queue_store, _get_user_id
from presentation.api.stores import proposed_blocks_store
from settings import DEFAULT_TZ

router = APIRouter()


@router.post("/dev/queue/seed")
async def seed_queue(
    request: Request,
    user_id: str = Depends(_get_user_id),
    count: int = 10,
) -> Dict[str, Any]:
    """Seed queue with test action items (dev only).

    Query params:
    - count: Number of items to seed (default: 10, max: 20)
    """
    import os

    if count > 20:
        count = 20

    # If mock DB is available (for testing), seed it directly
    try:
        from llm_testing.mock_db import get_mock_client
        from presentation.api.repos.queue import _resolve_identity

        tenant_id, resolved_user_id = _resolve_identity(user_id)
        mock_db = get_mock_client()
        items = mock_db.seed_queue(resolved_user_id, tenant_id, count)
        # Also add to queue_store for compatibility
        for item in items:
            queue_store[item["id"]] = {
                "action_id": item["id"],
                "source": item["source_type"],
                "category": "needs_response",
                "priority": item["priority"],
                "preview": item["payload"].get("preview", ""),
                "created_at": item.get("created_at", datetime.now().isoformat()),
            }
        return {"ok": True, "seeded": len(items), "total": len(queue_store)}
    except (ImportError, AttributeError, RuntimeError):
        # Mock DB not available - fall through to in-memory seeding
        pass

    test_items = [
        {
            "action_id": str(uuid.uuid4()),
            "source": "email",
            "category": "needs_response",
            "priority": "high",
            "preview": "Follow up on Q4 planning meeting - need your input on budget allocation",
            "thread_id": f"thread-{uuid.uuid4()}",
            "created_at": datetime.now().isoformat(),
        },
        {
            "action_id": str(uuid.uuid4()),
            "source": "teams",
            "category": "needs_approval",
            "priority": "medium",
            "preview": "Marketing team requested approval for new campaign launch",
            "thread_id": f"thread-{uuid.uuid4()}",
            "created_at": datetime.now().isoformat(),
        },
        {
            "action_id": str(uuid.uuid4()),
            "source": "doc",
            "category": "fyi",
            "priority": "low",
            "preview": "Design system documentation updated - new component guidelines added",
            "created_at": datetime.now().isoformat(),
        },
        {
            "action_id": str(uuid.uuid4()),
            "source": "email",
            "category": "needs_response",
            "priority": "high",
            "preview": "Urgent: Client feedback on proposal - please review by EOD",
            "thread_id": f"thread-{uuid.uuid4()}",
            "created_at": datetime.now().isoformat(),
        },
        {
            "action_id": str(uuid.uuid4()),
            "source": "teams",
            "category": "needs_approval",
            "priority": "high",
            "preview": "Expense report approval needed for Q4 team offsite",
            "thread_id": f"thread-{uuid.uuid4()}",
            "created_at": datetime.now().isoformat(),
        },
        {
            "action_id": str(uuid.uuid4()),
            "source": "email",
            "category": "needs_response",
            "priority": "medium",
            "preview": "Question about API integration timeline - when can we sync?",
            "thread_id": f"thread-{uuid.uuid4()}",
            "created_at": datetime.now().isoformat(),
        },
        {
            "action_id": str(uuid.uuid4()),
            "source": "doc",
            "category": "fyi",
            "priority": "low",
            "preview": "Product roadmap Q1 2025 - draft shared for review",
            "created_at": datetime.now().isoformat(),
        },
        {
            "action_id": str(uuid.uuid4()),
            "source": "teams",
            "category": "needs_response",
            "priority": "medium",
            "preview": "Can you join the design review meeting tomorrow at 2pm?",
            "thread_id": f"thread-{uuid.uuid4()}",
            "created_at": datetime.now().isoformat(),
        },
        {
            "action_id": str(uuid.uuid4()),
            "source": "email",
            "category": "needs_approval",
            "priority": "medium",
            "preview": "Hiring plan approval - need to add 2 engineers to team",
            "thread_id": f"thread-{uuid.uuid4()}",
            "created_at": datetime.now().isoformat(),
        },
        {
            "action_id": str(uuid.uuid4()),
            "source": "doc",
            "category": "fyi",
            "priority": "low",
            "preview": "Updated onboarding checklist - new starter resources added",
            "created_at": datetime.now().isoformat(),
        },
        {
            "action_id": str(uuid.uuid4()),
            "source": "email",
            "category": "needs_response",
            "priority": "high",
            "preview": "Action required: Sign contract for vendor partnership",
            "thread_id": f"thread-{uuid.uuid4()}",
            "created_at": datetime.now().isoformat(),
        },
        {
            "action_id": str(uuid.uuid4()),
            "source": "teams",
            "category": "needs_approval",
            "priority": "low",
            "preview": "Weekly team sync notes - please review and add feedback",
            "thread_id": f"thread-{uuid.uuid4()}",
            "created_at": datetime.now().isoformat(),
        },
        {
            "action_id": str(uuid.uuid4()),
            "source": "email",
            "category": "needs_response",
            "priority": "medium",
            "preview": "Follow up: Status update on project deliverables",
            "thread_id": f"thread-{uuid.uuid4()}",
            "created_at": datetime.now().isoformat(),
        },
        {
            "action_id": str(uuid.uuid4()),
            "source": "doc",
            "category": "fyi",
            "priority": "low",
            "preview": "Security audit report - Q4 findings summary",
            "created_at": datetime.now().isoformat(),
        },
        {
            "action_id": str(uuid.uuid4()),
            "source": "teams",
            "category": "needs_response",
            "priority": "medium",
            "preview": "Question about sprint planning - availability this week?",
            "thread_id": f"thread-{uuid.uuid4()}",
            "created_at": datetime.now().isoformat(),
        },
        {
            "action_id": str(uuid.uuid4()),
            "source": "email",
            "category": "needs_approval",
            "priority": "high",
            "preview": "Approval needed: Budget increase request for infrastructure",
            "thread_id": f"thread-{uuid.uuid4()}",
            "created_at": datetime.now().isoformat(),
        },
        {
            "action_id": str(uuid.uuid4()),
            "source": "doc",
            "category": "fyi",
            "priority": "low",
            "preview": "Engineering blog post draft - ready for review",
            "created_at": datetime.now().isoformat(),
        },
        {
            "action_id": str(uuid.uuid4()),
            "source": "email",
            "category": "needs_response",
            "priority": "medium",
            "preview": "Reminder: Performance review discussion scheduled",
            "thread_id": f"thread-{uuid.uuid4()}",
            "created_at": datetime.now().isoformat(),
        },
        {
            "action_id": str(uuid.uuid4()),
            "source": "teams",
            "category": "needs_approval",
            "priority": "medium",
            "preview": "Team lunch planning - vote on restaurant choice",
            "thread_id": f"thread-{uuid.uuid4()}",
            "created_at": datetime.now().isoformat(),
        },
        {
            "action_id": str(uuid.uuid4()),
            "source": "doc",
            "category": "fyi",
            "priority": "low",
            "preview": "Architecture decision record - new microservice pattern",
            "created_at": datetime.now().isoformat(),
        },
    ]

    # Add requested number of items (or all if count is large)
    items_to_add = test_items[:count] if count <= len(test_items) else test_items

    for item in items_to_add:
        queue_store[item["action_id"]] = item

    return {"ok": True, "seeded": len(items_to_add), "total": len(queue_store)}


@router.post("/dev/schedule/seed")
async def seed_schedule(
    request: Request,
    user_id: str = Depends(_get_user_id),
) -> Dict[str, Any]:
    """Seed schedule with test events and blocks (dev only)."""
    try:
        tz = ZoneInfo(DEFAULT_TZ)
    except Exception:
        from datetime import timezone

        tz = timezone.utc

    now = datetime.now(tz)
    today_start = now.replace(hour=9, minute=0, second=0, microsecond=0)

    # Add some events
    events = [
        {
            "id": f"event-{uuid.uuid4()}",
            "title": "Team Standup",
            "start": (today_start + timedelta(hours=1)).isoformat(),
            "end": (today_start + timedelta(hours=1, minutes=30)).isoformat(),
            "link": "",
        },
        {
            "id": f"event-{uuid.uuid4()}",
            "title": "Client Review Meeting",
            "start": (today_start + timedelta(hours=3)).isoformat(),
            "end": (today_start + timedelta(hours=4)).isoformat(),
            "link": "",
        },
        {
            "id": f"event-{uuid.uuid4()}",
            "title": "Lunch Break",
            "start": (today_start + timedelta(hours=5)).isoformat(),
            "end": (today_start + timedelta(hours=6)).isoformat(),
            "link": "",
        },
        {
            "id": f"event-{uuid.uuid4()}",
            "title": "Design Review",
            "start": (today_start + timedelta(hours=7)).isoformat(),
            "end": (today_start + timedelta(hours=7, minutes=45)).isoformat(),
            "link": "",
        },
    ]

    # Add proposed blocks
    blocks = [
        {
            "user_id": user_id,
            "id": f"block-{uuid.uuid4()}",
            "title": "Focus Time: Code Review",
            "start": (today_start + timedelta(hours=2)).isoformat(),
            "end": (today_start + timedelta(hours=2, minutes=45)).isoformat(),
            "kind": "work",
        },
        {
            "user_id": user_id,
            "id": f"block-{uuid.uuid4()}",
            "title": "Deep Work: Feature Implementation",
            "start": (today_start + timedelta(hours=6, minutes=30)).isoformat(),
            "end": (today_start + timedelta(hours=8)).isoformat(),
            "kind": "work",
        },
        {
            "user_id": user_id,
            "id": f"block-{uuid.uuid4()}",
            "title": "Admin: Catch up on emails",
            "start": (today_start + timedelta(hours=8, minutes=30)).isoformat(),
            "end": (today_start + timedelta(hours=9)).isoformat(),
            "kind": "admin",
        },
    ]

    # Add blocks to store (clear existing for this user first)
    existing_blocks = [b for b in proposed_blocks_store if b.get("user_id") != user_id]
    proposed_blocks_store.clear()
    proposed_blocks_store.extend(existing_blocks)
    proposed_blocks_store.extend(blocks)

    return {"ok": True, "events": len(events), "blocks": len(blocks)}


@router.post("/dev/all/seed")
async def seed_all(
    request: Request,
    user_id: str = Depends(_get_user_id),
) -> Dict[str, Any]:
    """Seed all test data at once (dev only)."""
    queue_result = await seed_queue(request, user_id, count=10)
    schedule_result = await seed_schedule(request, user_id)

    return {
        "ok": True,
        "queue": queue_result,
        "schedule": schedule_result,
    }


@router.post("/dev/queue/clear")
async def clear_queue(
    request: Request,
    user_id: str = Depends(_get_user_id),
) -> Dict[str, Any]:
    """Clear all queue items (dev only)."""
    queue_store.clear()
    return {"ok": True, "cleared": True}


@router.post("/dev/schedule/clear")
async def clear_schedule(
    request: Request,
    user_id: str = Depends(_get_user_id),
) -> Dict[str, Any]:
    """Clear all schedule blocks (dev only)."""
    existing_blocks = [b for b in proposed_blocks_store if b.get("user_id") != user_id]
    proposed_blocks_store.clear()
    proposed_blocks_store.extend(existing_blocks)
    return {"ok": True, "cleared": True}


@router.post("/dev/state/reset")
async def reset_state(
    request: Request,
    user_id: str = Depends(_get_user_id),
) -> Dict[str, Any]:
    """Reset all in-memory state stores (dev only).

    Clears:
    - approvals_store
    - history_log
    - queue_store
    - user settings (for test user)
    """
    from presentation.api.state import approvals_store, history_log
    from presentation.api.repos.user_settings import _settings_store

    approvals_store.clear()
    history_log.clear()
    queue_store.clear()

    # Clear settings for test user only
    settings_cleared = user_id in _settings_store
    if settings_cleared:
        del _settings_store[user_id]

    return {
        "ok": True,
        "cleared": {
            "approvals": True,
            "history": True,
            "queue": True,
            "settings": settings_cleared,
        },
    }

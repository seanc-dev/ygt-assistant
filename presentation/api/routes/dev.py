"""Dev endpoint to seed queue with test data."""
from __future__ import annotations
from typing import Any, Dict
from fastapi import APIRouter
import uuid
from datetime import datetime
from presentation.api.routes.queue import queue_store

router = APIRouter()


@router.post("/dev/queue/seed")
async def seed_queue() -> Dict[str, Any]:
    """Seed queue with test action items (dev only)."""
    test_items = [
        {
            "action_id": str(uuid.uuid4()),
            "source": "email",
            "category": "needs_response",
            "priority": "high",
            "preview": "Follow up on Q4 planning meeting - need your input on budget allocation",
            "created_at": datetime.now().isoformat(),
        },
        {
            "action_id": str(uuid.uuid4()),
            "source": "teams",
            "category": "needs_approval",
            "priority": "medium",
            "preview": "Marketing team requested approval for new campaign launch",
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
    ]
    
    for item in test_items:
        queue_store[item["action_id"]] = item
    
    return {"ok": True, "seeded": len(test_items)}


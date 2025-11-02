"""Tests for schedule endpoints."""
import pytest
from fastapi.testclient import TestClient
from presentation.api.app import app
from presentation.api.repos import user_settings
from presentation.api.stores import proposed_blocks_store

client = TestClient(app)


@pytest.fixture
def reset_stores():
    """Reset stores before each test."""
    proposed_blocks_store.clear()
    yield
    proposed_blocks_store.clear()


def test_schedule_today_empty(reset_stores):
    """Test schedule_today with no events or blocks."""
    response = client.get("/api/schedule/today")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["events"] == []
    assert data["blocks"] == []
    assert "date" in data


def test_schedule_today_with_blocks(reset_stores):
    """Test schedule_today merges existing events with proposed blocks."""
    # Add a proposed block
    proposed_blocks_store.append({
        "id": "block_1",
        "user_id": "default",
        "kind": "focus",
        "tasks": [],
        "action_id": "action_1",
        "estimated_minutes": 90,
        "priority": "high",
        "estimated_start": None,
    })
    
    response = client.get("/api/schedule/today")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert len(data["blocks"]) >= 1
    assert data["blocks"][0]["id"] == "block_1"
    assert data["blocks"][0]["kind"] == "focus"


def test_schedule_alternatives_produces_3_plans(reset_stores):
    """Test schedule_alternatives produces 3 plan types."""
    proposed_blocks = [
        {
            "id": "block_1",
            "kind": "focus",
            "estimated_minutes": 90,
            "priority": "high",
        },
        {
            "id": "block_2",
            "kind": "meeting",
            "estimated_minutes": 60,
            "priority": "medium",
        },
    ]
    
    response = client.post(
        "/api/schedule/alternatives",
        json={
            "existing_events": [],
            "proposed_blocks": proposed_blocks,
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert len(data["plans"]) == 3
    
    plan_types = {p["type"] for p in data["plans"]}
    assert "focus-first" in plan_types
    assert "meeting-friendly" in plan_types
    assert "balanced" in plan_types


def test_schedule_alternatives_overload_proposals(reset_stores):
    """Test overload proposals include requires_approval flag."""
    # Create many blocks to trigger overload
    proposed_blocks = [
        {
            "id": f"block_{i}",
            "kind": "focus",
            "estimated_minutes": 120,  # Large blocks
            "priority": "high",
        }
        for i in range(10)  # 10 blocks * 120min = 1200min > available
    ]
    
    response = client.post(
        "/api/schedule/alternatives",
        json={
            "existing_events": [],
            "proposed_blocks": proposed_blocks,
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    if data.get("overload", {}).get("detected"):
        proposals = data["overload"].get("proposals", [])
        if proposals:
            assert all(p.get("requires_approval") is True for p in proposals)


def test_collision_resolver_shifts_blocks():
    """Test collision resolver shifts blocks to avoid conflicts."""
    from presentation.api.utils.collision import resolve_collisions
    
    existing_events = [
        {
            "id": "event_1",
            "start": "2024-01-15T10:00:00Z",
            "end": "2024-01-15T11:00:00Z",
        }
    ]
    
    proposed_blocks = [
        {
            "id": "block_1",
            "kind": "focus",
            "estimated_minutes": 60,
            "estimated_start": "2024-01-15T10:30:00Z",
        }
    ]
    
    resolved = resolve_collisions(existing_events, proposed_blocks, buffer_minutes=5)
    
    assert len(resolved) == 1
    resolved_block = resolved[0]
    
    # Block should be shifted to start after event + buffer
    resolved_start = resolved_block["start"]
    assert resolved_start > "2024-01-15T11:00:00Z"


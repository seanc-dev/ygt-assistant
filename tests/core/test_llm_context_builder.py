"""Tests for LLM context builder."""

import pytest
from unittest.mock import Mock, patch
from core.services.llm_context_builder import build_context_for_user


@patch("presentation.api.repos.workroom")
@patch("presentation.api.repos.queue")
@patch("presentation.api.repos.tasks")
def test_build_context_for_user(mock_tasks, mock_queue, mock_workroom):
    """Test context builder loads user-scoped data."""
    # Mock repos
    mock_workroom.get_projects.return_value = [
        {"id": "proj-1", "name": "Project 1", "description": "Desc", "status": "active"}
    ]
    mock_workroom.get_tasks.return_value = [
        {"id": "task-1", "title": "Task 1", "status": "backlog", "priority": "medium"}
    ]
    mock_queue.get_queue_items.return_value = [
        {
            "id": "action-1",
            "source_type": "email",
            "priority": "high",
            "state": "queued",
            "payload": {"preview": "Test"},
        }
    ]

    context = build_context_for_user("tenant-1", "user-1")

    assert len(context["projects"]) == 1
    assert len(context["tasks"]) == 1
    assert len(context["actions"]) == 1
    assert context["focus_item"] is None


@patch("presentation.api.repos.workroom")
@patch("presentation.api.repos.queue")
@patch("presentation.api.repos.tasks")
def test_build_context_with_focus_action(mock_tasks, mock_queue, mock_workroom):
    """Test context builder includes focus action."""
    mock_workroom.get_projects.return_value = []
    mock_workroom.get_tasks.return_value = []
    mock_queue.get_queue_items.return_value = []
    mock_tasks.get_action_item.return_value = {
        "id": "action-1",
        "source_type": "email",
        "priority": "high",
        "state": "queued",
        "payload": {"preview": "Test action"},
    }

    context = build_context_for_user("tenant-1", "user-1", focus_action_id="action-1")

    assert context["focus_item"] is not None
    assert context["focus_item"]["type"] == "action"
    assert context["focus_item"]["id"] == "action-1"


@patch("presentation.api.repos.workroom")
@patch("presentation.api.repos.queue")
@patch("presentation.api.repos.tasks")
def test_build_context_respects_limits(mock_tasks, mock_queue, mock_workroom):
    """Test context builder respects max limits."""
    # Create many items
    mock_workroom.get_projects.return_value = [
        {"id": f"proj-{i}", "name": f"Project {i}"} for i in range(30)
    ]
    mock_workroom.get_tasks.return_value = [
        {"id": f"task-{i}", "title": f"Task {i}"} for i in range(60)
    ]
    mock_queue.get_queue_items.return_value = [
        {"id": f"action-{i}", "source_type": "email", "payload": {}} for i in range(25)
    ]

    context = build_context_for_user(
        "tenant-1", "user-1", max_projects=20, max_tasks=50, max_actions=20
    )

    assert len(context["projects"]) == 20
    assert len(context["tasks"]) == 50
    assert len(context["actions"]) == 20

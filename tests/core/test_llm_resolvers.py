"""Tests for semantic reference resolution helpers."""

import pytest
from unittest.mock import patch
from core.services.llm_executor import (
    _resolve_project_id,
    _resolve_task_id,
    _resolve_action_id,
    MultipleMatchesError,
)


class TestResolveProjectId:
    """Tests for _resolve_project_id."""

    def test_resolve_by_uuid(self):
        """Test resolving a UUID directly."""
        uuid_ref = "123e4567-e89b-12d3-a456-426614174000"
        result = _resolve_project_id(uuid_ref, None, None, None)
        assert result == uuid_ref

    def test_resolve_by_name(self):
        """Test resolving a project by name."""
        context = {
            "projects": [
                {"id": "proj-1", "name": "My Project"},
                {"id": "proj-2", "name": "Another Project"},
            ]
        }
        result = _resolve_project_id("My Project", context, None, None)
        assert result == "proj-1"

    def test_resolve_current_project(self):
        """Test resolving 'current project' alias."""
        context = {
            "projects": [{"id": "proj-1", "name": "My Project"}],
            "tasks": [{"id": "task-1", "project_id": "proj-1"}],
        }
        with patch("presentation.api.repos.workroom.get_task") as mock_get_task:
            mock_get_task.return_value = {"project_id": "proj-1"}
            result = _resolve_project_id("current project", context, "task-1", "user-1")
            assert result == "proj-1"

    def test_resolve_current_project_no_focus_task(self):
        """Test 'current project' without focus task returns None."""
        result = _resolve_project_id("current project", None, None, None)
        assert result is None

    def test_resolve_multiple_matches_raises_error(self):
        """Test that multiple matches raise MultipleMatchesError."""
        context = {
            "projects": [
                {"id": "proj-1", "name": "My Project"},
                {"id": "proj-2", "name": "My Project"},  # Duplicate name
            ]
        }
        with pytest.raises(MultipleMatchesError) as exc_info:
            _resolve_project_id("My Project", context, None, None)
        assert "Multiple projects" in str(exc_info.value)

    def test_resolve_not_found_returns_none(self):
        """Test that non-existent project returns None."""
        context = {"projects": [{"id": "proj-1", "name": "My Project"}]}
        result = _resolve_project_id("Non-existent", context, None, None)
        assert result is None

    def test_resolve_case_insensitive(self):
        """Test that resolution is case-insensitive."""
        context = {"projects": [{"id": "proj-1", "name": "My Project"}]}
        result = _resolve_project_id("my project", context, None, None)
        assert result == "proj-1"

    def test_resolve_with_user_id_fallback(self):
        """Test that resolver falls back to loading projects if context not provided."""
        with patch("presentation.api.repos.workroom.get_projects") as mock_get_projects:
            mock_get_projects.return_value = [
                {"id": "proj-1", "name": "My Project"}
            ]
            result = _resolve_project_id("My Project", None, None, "user-1")
            assert result == "proj-1"


class TestResolveTaskId:
    """Tests for _resolve_task_id."""

    def test_resolve_by_uuid(self):
        """Test resolving a UUID directly."""
        uuid_ref = "123e4567-e89b-12d3-a456-426614174000"
        result = _resolve_task_id(uuid_ref, None, None, None)
        assert result == uuid_ref

    def test_resolve_by_title(self):
        """Test resolving a task by title."""
        context = {
            "tasks": [
                {"id": "task-1", "title": "Do something"},
                {"id": "task-2", "title": "Do something else"},
            ]
        }
        result = _resolve_task_id("Do something", context, None, None)
        assert result == "task-1"

    def test_resolve_this_task_alias(self):
        """Test resolving 'this task' alias."""
        result = _resolve_task_id("this task", None, "task-123", None)
        assert result == "task-123"

    def test_resolve_this_task_no_focus_raises_error(self):
        """Test that 'this task' without focus task raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            _resolve_task_id("this task", None, None, None)
        assert "requires a focus task" in str(exc_info.value)

    def test_resolve_multiple_matches_raises_error(self):
        """Test that multiple matches raise MultipleMatchesError."""
        context = {
            "tasks": [
                {"id": "task-1", "title": "Do something"},
                {"id": "task-2", "title": "Do something"},  # Duplicate title
            ]
        }
        with pytest.raises(MultipleMatchesError) as exc_info:
            _resolve_task_id("Do something", context, None, None)
        assert "Multiple tasks" in str(exc_info.value)

    def test_resolve_not_found_raises_error(self):
        """Test that non-existent task raises ValueError."""
        context = {"tasks": [{"id": "task-1", "title": "Do something"}]}
        with pytest.raises(ValueError) as exc_info:
            _resolve_task_id("Non-existent", context, None, None)
        assert "not found" in str(exc_info.value)

    def test_resolve_case_insensitive(self):
        """Test that resolution is case-insensitive."""
        context = {"tasks": [{"id": "task-1", "title": "Do Something"}]}
        result = _resolve_task_id("do something", context, None, None)
        assert result == "task-1"

    def test_resolve_with_user_id_fallback(self):
        """Test that resolver falls back to loading tasks if context not provided."""
        with patch("presentation.api.repos.workroom.get_tasks") as mock_get_tasks:
            mock_get_tasks.return_value = [
                {"id": "task-1", "title": "Do something"}
            ]
            result = _resolve_task_id("Do something", None, None, "user-1")
            assert result == "task-1"


class TestResolveActionId:
    """Tests for _resolve_action_id."""

    def test_resolve_by_uuid(self):
        """Test resolving a UUID directly."""
        uuid_ref = "123e4567-e89b-12d3-a456-426614174000"
        result = _resolve_action_id(uuid_ref, None, None, None)
        assert result == uuid_ref

    def test_resolve_by_preview(self):
        """Test resolving an action by preview."""
        context = {
            "actions": [
                {"id": "action-1", "preview": "Review document"},
                {"id": "action-2", "preview": "Reply to email"},
            ]
        }
        result = _resolve_action_id("Review document", context, None, None)
        assert result == "action-1"

    def test_resolve_by_payload_preview(self):
        """Test resolving an action by payload.preview."""
        context = {
            "actions": [
                {
                    "id": "action-1",
                    "payload": {"preview": "Review document"},
                }
            ]
        }
        result = _resolve_action_id("Review document", context, None, None)
        assert result == "action-1"

    def test_resolve_by_payload_subject(self):
        """Test resolving an action by payload.subject."""
        context = {
            "actions": [
                {
                    "id": "action-1",
                    "payload": {"subject": "Review document"},
                }
            ]
        }
        result = _resolve_action_id("Review document", context, None, None)
        assert result == "action-1"

    def test_resolve_multiple_matches_raises_error(self):
        """Test that multiple matches raise MultipleMatchesError."""
        context = {
            "actions": [
                {"id": "action-1", "preview": "Review document"},
                {"id": "action-2", "preview": "Review document"},  # Duplicate
            ]
        }
        with pytest.raises(MultipleMatchesError) as exc_info:
            _resolve_action_id("Review document", context, None, None)
        assert "Multiple actions" in str(exc_info.value)

    def test_resolve_not_found_raises_error(self):
        """Test that non-existent action raises ValueError."""
        context = {"actions": [{"id": "action-1", "preview": "Review document"}]}
        with pytest.raises(ValueError) as exc_info:
            _resolve_action_id("Non-existent", context, None, None)
        assert "not found" in str(exc_info.value)

    def test_resolve_case_insensitive(self):
        """Test that resolution is case-insensitive."""
        context = {"actions": [{"id": "action-1", "preview": "Review Document"}]}
        result = _resolve_action_id("review document", context, None, None)
        assert result == "action-1"

    def test_resolve_with_user_id_fallback(self):
        """Test that resolver falls back to loading actions if context not provided."""
        with patch("presentation.api.repos.queue.get_queue_items") as mock_get_queue_items:
            mock_get_queue_items.return_value = [
                {"id": "action-1", "preview": "Review document"}
            ]
            result = _resolve_action_id("Review document", None, None, "user-1")
            assert result == "action-1"


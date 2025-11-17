"""Tests for duplicate name validation in workroom repos."""

import pytest
from unittest.mock import patch
from presentation.api.repos.workroom import (
    create_project,
    create_task,
    DuplicateProjectNameError,
    DuplicateTaskTitleError,
)


@patch("presentation.api.repos.workroom._resolve_identity")
@patch("presentation.api.repos.workroom.get_projects")
@patch("presentation.api.repos.workroom._insert")
def test_create_project_duplicate_name(mock_insert, mock_get_projects, mock_resolve):
    """Test that creating a project with duplicate name raises DuplicateProjectNameError."""
    mock_resolve.return_value = ("tenant-1", "user-1")
    mock_get_projects.return_value = [
        {"id": "proj-1", "name": "My Project", "deleted_at": None}
    ]

    with pytest.raises(DuplicateProjectNameError) as exc_info:
        create_project("user-1", "My Project")
    
    assert "already exists" in str(exc_info.value)
    mock_insert.assert_not_called()


@patch("presentation.api.repos.workroom._resolve_identity")
@patch("presentation.api.repos.workroom.get_projects")
@patch("presentation.api.repos.workroom._insert")
def test_create_project_duplicate_name_case_insensitive(mock_insert, mock_get_projects, mock_resolve):
    """Test that duplicate detection is case-insensitive."""
    mock_resolve.return_value = ("tenant-1", "user-1")
    mock_get_projects.return_value = [
        {"id": "proj-1", "name": "My Project", "deleted_at": None}
    ]

    with pytest.raises(DuplicateProjectNameError):
        create_project("user-1", "my project")  # Different case
    
    mock_insert.assert_not_called()


@patch("presentation.api.repos.workroom._resolve_identity")
@patch("presentation.api.repos.workroom.get_projects")
@patch("presentation.api.repos.workroom._insert")
def test_create_project_unique_name_succeeds(mock_insert, mock_get_projects, mock_resolve):
    """Test that creating a project with unique name succeeds."""
    mock_resolve.return_value = ("tenant-1", "user-1")
    mock_get_projects.return_value = [
        {"id": "proj-1", "name": "Existing Project", "deleted_at": None}
    ]
    mock_insert.return_value = {"id": "proj-2", "name": "New Project"}

    result = create_project("user-1", "New Project")
    
    assert result["name"] == "New Project"
    mock_insert.assert_called_once()


@patch("presentation.api.repos.workroom._resolve_identity")
@patch("presentation.api.repos.workroom.get_projects")
@patch("presentation.api.repos.workroom.get_tasks")
@patch("presentation.api.repos.workroom._insert")
def test_create_task_duplicate_title(mock_insert, mock_get_tasks, mock_get_projects, mock_resolve):
    """Test that creating a task with duplicate title raises DuplicateTaskTitleError."""
    mock_resolve.return_value = ("tenant-1", "user-1")
    mock_get_projects.return_value = [
        {"id": "proj-1", "name": "My Project", "deleted_at": None}
    ]
    mock_get_tasks.return_value = [
        {"id": "task-1", "title": "Do something", "project_id": "proj-1", "deleted_at": None}
    ]

    with pytest.raises(DuplicateTaskTitleError) as exc_info:
        create_task("user-1", "Do something", project_id="proj-1")
    
    assert "already has a task with that name" in str(exc_info.value)
    mock_insert.assert_not_called()


@patch("presentation.api.repos.workroom._resolve_identity")
@patch("presentation.api.repos.workroom.get_projects")
@patch("presentation.api.repos.workroom.get_tasks")
@patch("presentation.api.repos.workroom._insert")
def test_create_task_duplicate_title_case_insensitive(mock_insert, mock_get_tasks, mock_get_projects, mock_resolve):
    """Test that duplicate task detection is case-insensitive."""
    mock_resolve.return_value = ("tenant-1", "user-1")
    mock_get_projects.return_value = [
        {"id": "proj-1", "name": "My Project", "deleted_at": None}
    ]
    mock_get_tasks.return_value = [
        {"id": "task-1", "title": "Do Something", "project_id": "proj-1", "deleted_at": None}
    ]

    with pytest.raises(DuplicateTaskTitleError):
        create_task("user-1", "do something", project_id="proj-1")  # Different case
    
    mock_insert.assert_not_called()


@patch("presentation.api.repos.workroom._resolve_identity")
@patch("presentation.api.repos.workroom.get_projects")
@patch("presentation.api.repos.workroom.get_tasks")
@patch("presentation.api.repos.workroom._insert")
def test_create_task_unique_title_succeeds(mock_insert, mock_get_tasks, mock_get_projects, mock_resolve):
    """Test that creating a task with unique title succeeds."""
    mock_resolve.return_value = ("tenant-1", "user-1")
    mock_get_projects.return_value = [
        {"id": "proj-1", "name": "My Project", "deleted_at": None}
    ]
    mock_get_tasks.return_value = [
        {"id": "task-1", "title": "Existing Task", "project_id": "proj-1", "deleted_at": None}
    ]
    mock_insert.return_value = {"id": "task-2", "title": "New Task"}

    result = create_task("user-1", "New Task", project_id="proj-1")
    
    assert result["title"] == "New Task"
    mock_insert.assert_called_once()


@patch("presentation.api.repos.workroom._resolve_identity")
@patch("presentation.api.repos.workroom.get_projects")
@patch("presentation.api.repos.workroom.get_tasks")
@patch("presentation.api.repos.workroom._insert")
def test_create_task_no_project_no_duplicate_check(mock_insert, mock_get_tasks, mock_get_projects, mock_resolve):
    """Test that tasks without project_id don't check for duplicates."""
    mock_resolve.return_value = ("tenant-1", "user-1")
    mock_get_projects.return_value = []
    mock_get_tasks.return_value = []
    mock_insert.return_value = {"id": "task-1", "title": "New Task"}

    result = create_task("user-1", "New Task", project_id=None)
    
    assert result["title"] == "New Task"
    mock_get_tasks.assert_not_called()  # No duplicate check when no project_id
    mock_insert.assert_called_once()


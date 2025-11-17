"""Tests for robust deleted_at filtering with fallback handling."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from presentation.api.app import app
import httpx


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_user_id():
    return "test-user-123"


@patch("presentation.api.repos.workroom._resolve_identity")
@patch("presentation.api.repos.workroom.client")
def test_get_projects_fallback_on_400_error(mock_client_factory, mock_resolve, mock_user_id):
    """Test that get_projects falls back to Python filtering when PostgREST returns 400."""
    from presentation.api.repos import workroom as workroom_repo
    
    mock_resolve.return_value = ("tenant-1", "user-1")
    
    # Mock client that raises 400 on first call (with deleted_at), succeeds on second (without)
    mock_client = MagicMock()
    mock_response_400 = MagicMock()
    mock_response_400.status_code = 400
    mock_response_400.raise_for_status.side_effect = httpx.HTTPStatusError(
        "400 Bad Request",
        request=MagicMock(),
        response=mock_response_400,
    )
    
    mock_response_200 = MagicMock()
    mock_response_200.status_code = 200
    mock_response_200.json.return_value = [
        {"id": "proj-1", "name": "Project 1", "deleted_at": None},
        {"id": "proj-2", "name": "Project 2", "deleted_at": "2024-01-01T00:00:00Z"},
        {"id": "proj-3", "name": "Project 3", "deleted_at": None},
    ]
    
    # First call (with deleted_at) fails, second call (without) succeeds
    mock_client.get.side_effect = [
        mock_response_400,  # First call with deleted_at fails
        mock_response_200,   # Second call without deleted_at succeeds
    ]
    
    mock_client_factory.return_value.__enter__.return_value = mock_client
    
    # Call get_projects
    projects = workroom_repo.get_projects(mock_user_id)
    
    # Should filter out deleted project in Python
    assert len(projects) == 2
    assert projects[0]["id"] == "proj-1"
    assert projects[1]["id"] == "proj-3"
    assert all(p.get("deleted_at") is None for p in projects)
    
    # Verify two calls were made (first with deleted_at, second without)
    assert mock_client.get.call_count == 2


@patch("presentation.api.repos.workroom._resolve_identity")
@patch("presentation.api.repos.workroom.client")
def test_get_tasks_fallback_on_400_error(mock_client_factory, mock_resolve, mock_user_id):
    """Test that get_tasks falls back to Python filtering when PostgREST returns 400."""
    from presentation.api.repos import workroom as workroom_repo
    
    mock_resolve.return_value = ("tenant-1", "user-1")
    
    # Mock client that raises 400 on first call (with deleted_at), succeeds on second (without)
    mock_client = MagicMock()
    mock_response_400 = MagicMock()
    mock_response_400.status_code = 400
    mock_response_400.raise_for_status.side_effect = httpx.HTTPStatusError(
        "400 Bad Request",
        request=MagicMock(),
        response=mock_response_400,
    )
    
    mock_response_200 = MagicMock()
    mock_response_200.status_code = 200
    mock_response_200.json.return_value = [
        {"id": "task-1", "title": "Task 1", "deleted_at": None},
        {"id": "task-2", "title": "Task 2", "deleted_at": "2024-01-01T00:00:00Z"},
    ]
    
    mock_client.get.side_effect = [
        mock_response_400,  # First call with deleted_at fails
        mock_response_200,   # Second call without deleted_at succeeds
    ]
    
    mock_client_factory.return_value.__enter__.return_value = mock_client
    
    # Call get_tasks
    tasks = workroom_repo.get_tasks(mock_user_id, project_id="proj-1")
    
    # Should filter out deleted task in Python
    assert len(tasks) == 1
    assert tasks[0]["id"] == "task-1"
    assert tasks[0].get("deleted_at") is None
    
    # Verify two calls were made
    assert mock_client.get.call_count == 2


@patch("presentation.api.repos.workroom._resolve_identity")
@patch("presentation.api.repos.workroom.client")
def test_get_projects_success_with_deleted_at_filter(mock_client_factory, mock_resolve, mock_user_id):
    """Test that get_projects works correctly when deleted_at filter succeeds."""
    from presentation.api.repos import workroom as workroom_repo
    
    mock_resolve.return_value = ("tenant-1", "user-1")
    
    # Mock client that succeeds with deleted_at filter
    mock_client = MagicMock()
    mock_response_200 = MagicMock()
    mock_response_200.status_code = 200
    mock_response_200.json.return_value = [
        {"id": "proj-1", "name": "Project 1", "deleted_at": None, "order_index": 1},
        {"id": "proj-2", "name": "Project 2", "deleted_at": None, "order_index": 2},
    ]
    
    mock_client.get.return_value = mock_response_200
    mock_client_factory.return_value.__enter__.return_value = mock_client
    
    # Call get_projects
    projects = workroom_repo.get_projects(mock_user_id)
    
    # Should return all projects (already filtered by PostgREST)
    assert len(projects) == 2
    
    # Verify only one call was made (no fallback needed)
    assert mock_client.get.call_count == 1
    # Verify deleted_at filter was included in params
    call_args = mock_client.get.call_args
    assert "deleted_at" in call_args.kwargs.get("params", {})


@patch("presentation.api.repos.workroom._resolve_identity")
@patch("presentation.api.repos.workroom.client")
def test_get_projects_raises_non_400_errors(mock_client_factory, mock_resolve, mock_user_id):
    """Test that get_projects re-raises non-400 HTTP errors."""
    from presentation.api.repos import workroom as workroom_repo
    
    mock_resolve.return_value = ("tenant-1", "user-1")
    
    # Mock client that raises 500 error
    mock_client = MagicMock()
    mock_response_500 = MagicMock()
    mock_response_500.status_code = 500
    mock_response_500.raise_for_status.side_effect = httpx.HTTPStatusError(
        "500 Internal Server Error",
        request=MagicMock(),
        response=mock_response_500,
    )
    
    mock_client.get.return_value = mock_response_500
    mock_client_factory.return_value.__enter__.return_value = mock_client
    
    # Call get_projects - should raise the 500 error
    with pytest.raises(httpx.HTTPStatusError):
        workroom_repo.get_projects(mock_user_id)
    
    # Verify only one call was made (no fallback for non-400 errors)
    assert mock_client.get.call_count == 1


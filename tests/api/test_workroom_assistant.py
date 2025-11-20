"""Tests for workroom assistant-suggest endpoint."""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from presentation.api.app import app
from services.llm import LlmProposedContent


@pytest.fixture
def client():
    return TestClient(app)


@patch("presentation.api.routes.workroom.workroom_repo")
@patch("services.llm.propose_ops_for_user")
@patch("core.services.llm_executor.execute_ops")
@patch("presentation.api.repos.user_settings")
@patch("presentation.api.repos.workroom._resolve_identity")
@patch("presentation.api.routes.workroom.audit_log")
def test_assistant_suggest_for_task(
    mock_audit, mock_resolve, mock_settings, mock_execute, mock_llm, mock_workroom, client
):
    """Test assistant-suggest endpoint for task."""
    mock_resolve.return_value = ("tenant-1", "user-1")
    mock_settings.get_settings.return_value = {"trust_level": "supervised"}
    mock_workroom.get_task.return_value = {"id": "task-1", "title": "Test Task"}
    mock_llm.propose_ops_for_user.return_value = LlmProposedContent(
        operations=[
            {"op": "update_task_status", "params": {"task_id": "task-1", "status": "done"}},
        ],
        surfaces=[],
    )
    mock_execute.return_value = {
        "applied": [{"op": "update_task_status", "params": {"task_id": "task-1", "status": "done"}}],
        "pending": [],
        "errors": [],
    }
    
    response = client.post(
        "/api/workroom/tasks/task-1/assistant-suggest",
        json={"message": "Mark this as done"},
        cookies={"user_id": "test-user"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert len(data["applied"]) == 1


@patch("presentation.api.routes.workroom.workroom_repo")
@patch("services.llm.propose_ops_for_user")
@patch("core.services.llm_executor.execute_ops")
@patch("presentation.api.repos.user_settings")
@patch("presentation.api.repos.workroom._resolve_identity")
@patch("presentation.api.routes.workroom.audit_log")
@patch("presentation.api.routes.workroom._get_thread_lock", new_callable=AsyncMock)
def test_assistant_suggest_for_task_with_thread_id(
    mock_thread_lock,
    mock_audit,
    mock_resolve,
    mock_settings,
    mock_execute,
    mock_llm,
    mock_workroom,
    client,
):
    """Test assistant-suggest endpoint when only thread_id is provided."""
    mock_resolve.return_value = ("tenant-1", "user-1")
    mock_settings.get_settings.return_value = {"trust_level": "supervised"}
    mock_workroom.get_task.return_value = {"id": "task-1", "title": "Test Task", "thread_id": "thread-123"}
    mock_workroom.get_pending_user_messages.return_value = [{"content": "Do the thing"}]
    mock_llm.propose_ops_for_user.return_value = LlmProposedContent(
        operations=[
            {"op": "update_task_status", "params": {"task_id": "task-1", "status": "done"}},
        ],
        surfaces=[],
    )
    mock_execute.return_value = {
        "applied": [{"op": "update_task_status", "params": {"task_id": "task-1", "status": "done"}}],
        "pending": [],
        "errors": [],
    }
    lock_ctx = Mock()
    lock_ctx.__aenter__ = AsyncMock(return_value=None)
    lock_ctx.__aexit__ = AsyncMock(return_value=None)
    mock_thread_lock.return_value = lock_ctx

    response = client.post(
        "/api/workroom/tasks/task-1/assistant-suggest",
        json={"thread_id": "thread-123"},
        cookies={"user_id": "test-user"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True


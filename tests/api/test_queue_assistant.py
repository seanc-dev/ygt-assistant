"""Tests for queue assistant-suggest endpoint."""
import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from presentation.api.app import app


@pytest.fixture
def client():
    return TestClient(app)


@patch("presentation.api.repos.tasks")
@patch("services.llm.propose_ops_for_user")
@patch("core.services.llm_executor.execute_ops")
@patch("presentation.api.routes.queue.user_settings")
@patch("presentation.api.repos.workroom._resolve_identity")
@patch("presentation.api.routes.queue.audit_log")
def test_assistant_suggest_for_action(
    mock_audit, mock_resolve, mock_settings, mock_execute, mock_llm, mock_tasks, client
):
    """Test assistant-suggest endpoint for action."""
    mock_resolve.return_value = ("tenant-1", "user-1")
    mock_settings.get_settings.return_value = {"trust_level": "supervised"}
    mock_tasks.get_action_item.return_value = {"id": "action-1", "source_type": "email"}
    mock_llm.propose_ops_for_user.return_value = [
        {"op": "chat", "params": {"message": "Hello"}},
        {"op": "create_task", "params": {"title": "Test"}},
    ]
    mock_execute.return_value = {
        "applied": [{"op": "chat", "params": {"message": "Hello"}}],
        "pending": [{"op": "create_task", "params": {"title": "Test"}}],
        "errors": [],
    }
    
    response = client.post(
        "/api/queue/action-1/assistant-suggest",
        json={"message": "Create a task"},
        cookies={"user_id": "test-user"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert len(data["applied"]) == 1
    assert len(data["pending"]) == 1


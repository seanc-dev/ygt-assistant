"""E2E tests for project and task deletion via assistant-suggest endpoint."""
import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from presentation.api.app import app
from services.llm import LlmProposedContent


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_workroom_data():
    """Mock workroom data for testing."""
    return {
        "project": {"id": "project-1", "name": "Test Project", "deleted_at": None},
        "task": {"id": "task-1", "title": "Test Task", "project_id": "project-1", "deleted_at": None},
        "tasks_in_project": [
            {"id": "task-1", "title": "Task 1", "project_id": "project-1", "deleted_at": None},
            {"id": "task-2", "title": "Task 2", "project_id": "project-1", "deleted_at": None},
        ],
    }


@patch("presentation.api.routes.workroom.workroom_repo")
@patch("services.llm.propose_ops_for_user")
@patch("core.services.llm_executor.execute_ops")
@patch("presentation.api.repos.user_settings")
@patch("presentation.api.repos.workroom._resolve_identity")
@patch("presentation.api.routes.workroom.audit_log")
def test_delete_project_via_assistant_suggest(
    mock_audit,
    mock_resolve,
    mock_settings,
    mock_execute,
    mock_llm,
    mock_workroom,
    client,
    mock_workroom_data,
):
    """Test deleting a project via assistant-suggest endpoint."""
    mock_resolve.return_value = ("tenant-1", "user-1")
    mock_settings.get_settings.return_value = {"trust_level": "training_wheels"}
    mock_workroom.get_task.return_value = mock_workroom_data["task"]
    mock_workroom.get_projects.return_value = [mock_workroom_data["project"]]
    
    # LLM proposes delete_project operation
    mock_llm.propose_ops_for_user.return_value = LlmProposedContent(
        operations=[{"op": "delete_project", "params": {"project_ids": ["project-1"]}}],
        surfaces=[],
    )
    
    # Executor returns pending (training_wheels mode)
    mock_execute.return_value = {
        "applied": [],
        "pending": [{"op": "delete_project", "params": {"project_ids": ["project-1"]}}],
        "errors": [],
    }
    
    response = client.post(
        "/api/workroom/tasks/task-1/assistant-suggest",
        json={"message": "Delete the Test Project"},
        cookies={"user_id": "test-user"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert len(data["pending"]) == 1
    assert data["pending"][0]["op"] == "delete_project"
    assert "project-1" in data["pending"][0]["params"]["project_ids"]


@patch("presentation.api.routes.workroom.workroom_repo")
@patch("services.llm.propose_ops_for_user")
@patch("core.services.llm_executor.execute_ops")
@patch("presentation.api.repos.user_settings")
@patch("presentation.api.repos.workroom._resolve_identity")
@patch("presentation.api.routes.workroom.audit_log")
def test_delete_task_via_assistant_suggest(
    mock_audit,
    mock_resolve,
    mock_settings,
    mock_execute,
    mock_llm,
    mock_workroom,
    client,
    mock_workroom_data,
):
    """Test deleting a task via assistant-suggest endpoint."""
    mock_resolve.return_value = ("tenant-1", "user-1")
    mock_settings.get_settings.return_value = {"trust_level": "training_wheels"}
    mock_workroom.get_task.return_value = mock_workroom_data["task"]
    
    # LLM proposes delete_task operation
    mock_llm.propose_ops_for_user.return_value = LlmProposedContent(
        operations=[{"op": "delete_task", "params": {"task_ids": ["task-1"]}}],
        surfaces=[],
    )
    
    # Executor returns pending (training_wheels mode)
    mock_execute.return_value = {
        "applied": [],
        "pending": [{"op": "delete_task", "params": {"task_ids": ["task-1"]}}],
        "errors": [],
    }
    
    response = client.post(
        "/api/workroom/tasks/task-1/assistant-suggest",
        json={"message": "Delete this task"},
        cookies={"user_id": "test-user"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert len(data["pending"]) == 1
    assert data["pending"][0]["op"] == "delete_task"
    assert "task-1" in data["pending"][0]["params"]["task_ids"]


@patch("presentation.api.routes.workroom.workroom_repo")
@patch("services.llm.propose_ops_for_user")
@patch("core.services.llm_executor.execute_ops")
@patch("presentation.api.repos.user_settings")
@patch("presentation.api.repos.workroom._resolve_identity")
@patch("presentation.api.routes.workroom.audit_log")
def test_delete_project_autonomous_mode(
    mock_audit,
    mock_resolve,
    mock_settings,
    mock_execute,
    mock_llm,
    mock_workroom,
    client,
    mock_workroom_data,
):
    """Test deleting a project in autonomous mode (should be applied)."""
    mock_resolve.return_value = ("tenant-1", "user-1")
    mock_settings.get_settings.return_value = {"trust_level": "autonomous"}
    mock_workroom.get_task.return_value = mock_workroom_data["task"]
    mock_workroom.get_projects.return_value = [mock_workroom_data["project"]]
    
    # LLM proposes delete_project operation
    mock_llm.propose_ops_for_user.return_value = LlmProposedContent(
        operations=[{"op": "delete_project", "params": {"project_ids": ["project-1"]}}],
        surfaces=[],
    )
    
    # Executor applies the operation (autonomous mode)
    mock_execute.return_value = {
        "applied": [{"op": "delete_project", "params": {"project_ids": ["project-1"]}}],
        "pending": [],
        "errors": [],
    }
    
    response = client.post(
        "/api/workroom/tasks/task-1/assistant-suggest",
        json={"message": "Delete the Test Project"},
        cookies={"user_id": "test-user"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert len(data["applied"]) == 1
    assert data["applied"][0]["op"] == "delete_project"
    assert len(data["pending"]) == 0


@patch("presentation.api.routes.workroom.workroom_repo")
@patch("services.llm.propose_ops_for_user")
@patch("core.services.llm_executor.execute_ops")
@patch("presentation.api.repos.user_settings")
@patch("presentation.api.repos.workroom._resolve_identity")
@patch("presentation.api.routes.workroom.audit_log")
def test_delete_error_handling(
    mock_audit,
    mock_resolve,
    mock_settings,
    mock_execute,
    mock_llm,
    mock_workroom,
    client,
    mock_workroom_data,
):
    """Test graceful error handling when deletion fails."""
    mock_resolve.return_value = ("tenant-1", "user-1")
    mock_settings.get_settings.return_value = {"trust_level": "autonomous"}
    mock_workroom.get_task.return_value = mock_workroom_data["task"]
    
    # LLM proposes delete_project operation
    mock_llm.propose_ops_for_user.return_value = LlmProposedContent(
        operations=[{"op": "delete_project", "params": {"project_ids": ["non-existent"]}}],
        surfaces=[],
    )
    
    # Executor fails and generates error chat message
    mock_execute.return_value = {
        "applied": [
            {
                "op": "chat",
                "params": {
                    "message": "I couldn't delete the project: Project not found. Please check the project name and try again."
                },
            }
        ],
        "pending": [],
        "errors": [
            {"op": "delete_project", "params": {"project_ids": ["non-existent"]}, "error": "Project not found"},
        ],
    }
    
    response = client.post(
        "/api/workroom/tasks/task-1/assistant-suggest",
        json={"message": "Delete the Non-existent Project"},
        cookies={"user_id": "test-user"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert len(data["errors"]) == 1
    assert len(data["applied"]) == 1
    assert data["applied"][0]["op"] == "chat"
    assert "couldn't delete" in data["applied"][0]["params"]["message"].lower()


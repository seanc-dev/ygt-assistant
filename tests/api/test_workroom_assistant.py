"""Tests for workroom assistant-suggest endpoint."""
import pytest
from unittest.mock import Mock, patch, AsyncMock
import pytest
from fastapi.testclient import TestClient
from presentation.api.app import app
from services.llm import LlmProposedContent


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=True)


@patch("presentation.api.routes.workroom.build_workroom_context_space")
@patch("presentation.api.routes.workroom.audit_log")
@patch("presentation.api.repos.workroom._resolve_identity")
@patch("presentation.api.repos.user_settings")
@patch("core.services.llm_executor.execute_ops")
@patch("presentation.api.routes.workroom.llm_service.propose_ops_for_user")
@patch("presentation.api.routes.workroom.workroom_repo")
def test_assistant_suggest_for_task(
    mock_workroom,
    mock_llm,
    mock_execute,
    mock_settings,
    mock_resolve,
    mock_audit,
    mock_context_space,
    client,
):
    """Test assistant-suggest endpoint for task."""
    mock_resolve.return_value = ("tenant-1", "user-1")
    mock_settings.get_settings.return_value = {"trust_level": "supervised"}
    mock_workroom.get_task.return_value = {"id": "task-1", "title": "Test Task"}
    mock_context_space.return_value.to_context_input.return_value = {
        "anchor": {"task_id": "task-1", "project_id": None}
    }
    mock_llm.return_value = LlmProposedContent(
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
    assert mock_llm.call_args.kwargs["context_input"] == {
        "anchor": {"task_id": "task-1", "project_id": None}
    }


@patch("presentation.api.routes.workroom.build_workroom_context_space")
@patch("presentation.api.routes.workroom._get_thread_lock", new_callable=AsyncMock)
@patch("presentation.api.routes.workroom.audit_log")
@patch("presentation.api.repos.workroom._resolve_identity")
@patch("presentation.api.repos.user_settings")
@patch("core.services.llm_executor.execute_ops")
@patch("presentation.api.routes.workroom.llm_service.propose_ops_for_user")
@patch("presentation.api.routes.workroom.workroom_repo")
def test_assistant_suggest_for_task_with_thread_id(
    mock_workroom,
    mock_llm,
    mock_execute,
    mock_settings,
    mock_resolve,
    mock_audit,
    mock_thread_lock,
    mock_context_space,
    client,
):
    """Test assistant-suggest endpoint when only thread_id is provided."""
    mock_resolve.return_value = ("tenant-1", "user-1")
    mock_settings.get_settings.return_value = {"trust_level": "supervised"}
    mock_workroom.get_task.return_value = {"id": "task-1", "title": "Test Task", "thread_id": "thread-123"}
    mock_workroom.get_pending_user_messages.return_value = [{"content": "Do the thing"}]
    mock_context_space.return_value = None
    mock_llm.return_value = LlmProposedContent(
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
    assert "context_input" in mock_llm.call_args.kwargs
    assert mock_llm.call_args.kwargs["context_input"] is None


@patch("presentation.api.routes.workroom.workroom_repo")
@patch("services.llm.propose_ops_for_user")
@patch("core.services.llm_context_builder.build_context_for_user")
@patch("core.services.llm_executor.execute_ops")
@patch("presentation.api.repos.user_settings")
@patch("presentation.api.repos.workroom._resolve_identity")
@patch("presentation.api.routes.workroom.audit_log")
def test_assistant_suggest_filters_surfaces(
    mock_audit,
    mock_resolve,
    mock_settings,
    mock_execute,
    mock_context_builder,
    mock_llm,
    mock_workroom,
    client,
):
    mock_resolve.return_value = ("tenant-1", "user-1")
    mock_settings.get_settings.return_value = {"trust_level": "supervised"}
    mock_workroom.get_task.return_value = {"id": "task-1", "title": "Test Task", "priority": "high"}
    mock_context_builder.return_value = {
        "projects": [],
        "tasks": [
            {"id": "task-1", "title": "Test Task", "priority": "high"},
            {"id": "task-2", "title": "Other Task"},
        ],
        "actions": [
            {"id": "queue-1", "preview": "Email from CFO"},
        ],
    }
    mock_llm.return_value = LlmProposedContent(
        operations=[{"op": "chat", "params": {"message": "Sure"}}],
        surfaces=[
            {
                "surface_id": "s1",
                "kind": "priority_list_v1",
                "title": "Priorities",
                "payload": {"items": [{"rank": 1, "taskId": "task-1", "label": "Do it"}]},
            },
            {
                "surface_id": "s2",
                "kind": "priority_list_v1",
                "title": "Bad",
                "payload": {"items": [{"rank": 1, "taskId": "missing", "label": "Nope"}]},
            },
            {
                "surface_id": "s3",
                "kind": "triage_table_v1",
                "title": "Triage",
                "payload": {
                    "groups": [
                        {
                            "groupId": "g1",
                            "label": "Inbox",
                            "items": [
                                {
                                    "queueItemId": "queue-1",
                                    "source": "email",
                                    "subject": "Email from CFO",
                                    "approveOp": "approve",
                                    "declineOp": "decline",
                                }
                            ],
                        }
                    ]
                },
            },
            {
                "surface_id": "s4",
                "kind": "today_schedule_v1",
                "title": "Schedule",
                "payload": {
                    "blocks": [
                        {
                            "blockId": "b1",
                            "type": "event",
                            "eventId": "evt-missing",
                            "label": "Unknown event",
                            "start": "",
                            "end": "",
                            "isLocked": False,
                        }
                    ]
                },
            },
        ],
    )
    mock_execute.return_value = {"applied": [], "pending": [], "errors": []}

    response = client.post(
        "/api/workroom/tasks/task-1/assistant-suggest",
        json={"message": "What next?", "mode": "execute"},
        cookies={"user_id": "test-user"},
    )

    assert response.status_code == 200
    data = response.json()
    surface_ids = [s.get("surface_id") for s in data.get("surfaces", [])]
    assert surface_ids == ["s1", "s3"]
    attached_ids = [
        s.get("surface_id") for s in data["operations"][0]["params"].get("surfaces", [])
    ]
    assert attached_ids == ["s1", "s3"]

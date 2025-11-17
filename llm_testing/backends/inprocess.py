from __future__ import annotations
from typing import Any, Dict, List
from fastapi.testclient import TestClient  # type: ignore
import os
import sys


class InProcessBackend:
    def __init__(self) -> None:
        # Prepare minimal env for app import
        os.environ.setdefault("DEV_MODE", "true")
        os.environ.setdefault("USE_MOCK_GRAPH", "true")
        
        # Always set up mock database for tests (independent of LLM_TESTING_MODE)
        # LLM_TESTING_MODE controls LLM fixtures vs live calls
        # Mock DB ensures we don't hit real Supabase during testing
        self._setup_mock_db()

        try:
            from presentation.api.app import app  # type: ignore
        except Exception as exc:
            raise RuntimeError(f"FastAPI app not importable: {exc}")
        self.client = TestClient(app)

    def _setup_mock_db(self) -> None:
        """Set up mock database by patching the Supabase client."""
        from llm_testing.mock_db import get_mock_client, MockSupabaseClient

        # Create a context manager that returns our mock client
        class MockClientContext:
            def __init__(self, mock_client: MockSupabaseClient):
                self.mock_client = mock_client

            def __enter__(self):
                return self.mock_client

            def __exit__(self, *args):
                pass

        # Patch the client function to return our mock
        import archive.infra.supabase.client as client_module

        def mock_client():
            return MockClientContext(get_mock_client())

        # Monkey patch the client function before any repos import it
        client_module.client = mock_client

    # WhatsApp
    def whatsapp_verify(self, mode: str, token: str, challenge: str) -> str:
        r = self.client.get(
            "/whatsapp/webhook",
            params={"mode": mode, "token": token, "challenge": challenge},
        )
        r.raise_for_status()
        return r.text

    def whatsapp_post(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        r = self.client.post("/whatsapp/webhook", json=payload)
        r.raise_for_status()
        return r.json()

    # Actions
    def actions_scan(self, domains: List[str]) -> List[Dict[str, Any]]:
        r = self.client.post("/actions/scan", json={"domains": domains})
        r.raise_for_status()
        return r.json()

    def actions_approve(self, approval_id: str) -> Dict[str, Any]:
        r = self.client.post(f"/actions/approve/{approval_id}")
        r.raise_for_status()
        return r.json()

    def actions_edit(self, approval_id: str, instructions: str) -> Dict[str, Any]:
        r = self.client.post(
            f"/actions/edit/{approval_id}", json={"instructions": instructions}
        )
        r.raise_for_status()
        return r.json()

    def actions_skip(self, approval_id: str) -> Dict[str, Any]:
        r = self.client.post(f"/actions/skip/{approval_id}")
        r.raise_for_status()
        return r.json()

    def actions_undo(self, approval_id: str) -> Dict[str, Any]:
        r = self.client.post(f"/actions/undo/{approval_id}")
        r.raise_for_status()
        return r.json()

    # Email
    def email_create_draft(
        self, to: List[str], subject: str, body: str
    ) -> Dict[str, Any]:
        r = self.client.post(
            "/email/drafts", json={"to": to, "subject": subject, "body": body}
        )
        r.raise_for_status()
        return r.json()

    def email_send(self, draft_id: str) -> Dict[str, Any]:
        r = self.client.post(f"/email/send/{draft_id}")
        r.raise_for_status()
        return r.json()

    # Calendar
    def calendar_plan_today(self) -> Dict[str, Any]:
        r = self.client.post("/calendar/plan-today")
        r.raise_for_status()
        return r.json()

    # Approvals
    def approvals(self) -> List[Dict[str, Any]]:
        r = self.client.get("/approvals")
        r.raise_for_status()
        return r.json()

    def history(self, limit: int = 100) -> List[Dict[str, Any]]:
        r = self.client.get("/history", params={"limit": limit})
        r.raise_for_status()
        return r.json()

from __future__ import annotations
from typing import Any, Dict, List
import os
import httpx

BASE_URL = os.getenv("LLM_TESTING_BASE_URL", "http://localhost:8000")
TIMEOUT = 10.0


class HTTPBackend:
    def __init__(self) -> None:
        self.base = BASE_URL.rstrip("/")

    def _c(self) -> httpx.Client:
        return httpx.Client(base_url=self.base, timeout=TIMEOUT)

    # WhatsApp
    def whatsapp_verify(self, mode: str, token: str, challenge: str) -> str:
        with self._c() as c:
            r = c.get("/whatsapp/webhook", params={"mode": mode, "token": token, "challenge": challenge})
            r.raise_for_status()
            return r.text

    def whatsapp_post(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        with self._c() as c:
            r = c.post("/whatsapp/webhook", json=payload)
            r.raise_for_status()
            return r.json()

    # Actions
    def actions_scan(self, domains: List[str]) -> List[Dict[str, Any]]:
        with self._c() as c:
            r = c.post("/actions/scan", json={"domains": domains})
            r.raise_for_status()
            return r.json()

    def actions_approve(self, approval_id: str) -> Dict[str, Any]:
        with self._c() as c:
            r = c.post(f"/actions/approve/{approval_id}")
            r.raise_for_status()
            return r.json()

    def actions_edit(self, approval_id: str, instructions: str) -> Dict[str, Any]:
        with self._c() as c:
            r = c.post(f"/actions/edit/{approval_id}", json={"instructions": instructions})
            r.raise_for_status()
            return r.json()

    def actions_skip(self, approval_id: str) -> Dict[str, Any]:
        with self._c() as c:
            r = c.post(f"/actions/skip/{approval_id}")
            r.raise_for_status()
            return r.json()

    def actions_undo(self, approval_id: str) -> Dict[str, Any]:
        with self._c() as c:
            r = c.post(f"/actions/undo/{approval_id}")
            r.raise_for_status()
            return r.json()

    # Email
    def email_create_draft(self, to: List[str], subject: str, body: str) -> Dict[str, Any]:
        with self._c() as c:
            r = c.post("/email/drafts", json={"to": to, "subject": subject, "body": body})
            r.raise_for_status()
            return r.json()

    def email_send(self, draft_id: str) -> Dict[str, Any]:
        with self._c() as c:
            r = c.post(f"/email/send/{draft_id}")
            r.raise_for_status()
            return r.json()

    # Calendar
    def calendar_plan_today(self) -> Dict[str, Any]:
        with self._c() as c:
            r = c.post("/calendar/plan-today")
            r.raise_for_status()
            return r.json()

    # Approvals
    def approvals(self) -> List[Dict[str, Any]]:
        with self._c() as c:
            r = c.get("/approvals")
            r.raise_for_status()
            return r.json()

    def history(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self._c() as c:
            r = c.get("/history", params={"limit": limit})
            r.raise_for_status()
            return r.json()

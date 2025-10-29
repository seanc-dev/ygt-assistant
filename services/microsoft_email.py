from __future__ import annotations
from typing import Any, Dict, List
import os
import httpx

from services.providers.email_provider import EmailProvider
from services.providers.errors import ProviderError
from services.ms_auth import (
    ensure_access_token,
    ensure_access_token_sync,
    token_store_from_env,
)
from utils.metrics import increment
import uuid
import asyncio
from settings import GRAPH_TIMEOUT_MS, GRAPH_RETRY_MAX


class MicrosoftEmailProvider(EmailProvider):
    def __init__(self, user_id: str, tenant_id: str | None = None) -> None:
        self.user_id = user_id
        self.tenant_id = tenant_id or os.getenv("MS_TENANT_ID", "common")

    def _base(self) -> str:
        return "https://graph.microsoft.com/v1.0"

    async def _auth(self) -> str:
        # Prefer stored tokens; fallback to env token only if present
        row = None
        try:
            store = token_store_from_env()
            row = store.get(self.user_id)
        except Exception:
            row = None
        if row:
            # Avoid anyio.run when inside FastAPI event loop by using sync path
            return ensure_access_token_sync(self.user_id, row, self.tenant_id)
        tok = os.getenv("MS_TEST_ACCESS_TOKEN", "")
        if tok:
            return tok
        raise ProviderError(
            "microsoft",
            "auth",
            "missing access token",
            hint="Connect Microsoft account",
        )

    async def _request_with_retry(
        self,
        method: str,
        url: str,
        *,
        headers: Dict[str, str],
        params: Dict[str, Any] | None = None,
        json: Any | None = None,
        expected_status: List[int] | None = None,
        timeout: float = 10.0,
    ) -> httpx.Response:
        expected = set(expected_status or [200])
        backoff = 0.5
        last_exc: Exception | None = None
        req_id = str(uuid.uuid4())
        h = {**headers, "x-ms-client-request-id": req_id}
        for attempt in range(max(1, GRAPH_RETRY_MAX)):
            try:
                async with httpx.AsyncClient(timeout=GRAPH_TIMEOUT_MS / 1000.0) as c:
                    r = await c.request(
                        method, url, params=params, json=json, headers=h
                    )
                if r.status_code in expected:
                    return r
                # Allow callers to translate 401 into ProviderError with reconnect hint
                if r.status_code == 401:
                    return r
                if r.status_code in (429,) or 500 <= r.status_code < 600:
                    increment(
                        "ms.email.http.retry", status=r.status_code, attempt=attempt + 1
                    )
                    await asyncio.sleep(backoff)
                    backoff *= 2
                    continue
                r.raise_for_status()
                return r
            except Exception as exc:  # pragma: no cover - network
                last_exc = exc
                increment("ms.email.http.exception", attempt=attempt + 1)
                await asyncio.sleep(backoff)
                backoff *= 2
        # Exhausted retries
        if last_exc:
            raise last_exc
        raise ProviderError("microsoft", "http", "unexpected failure")

    def list_threads(self, q: str, max_n: int) -> List[Dict[str, Any]]:
        # Synchronous wrapper calls async quickly for MVP simplicity
        import anyio

        async def _run() -> List[Dict[str, Any]]:
            token = await self._auth()
            params = {
                "$top": str(max(1, min(max_n or 5, 25))),
                "$select": "subject,from,toRecipients,receivedDateTime,bodyPreview,webLink",
                "$orderby": "receivedDateTime desc",
                "$filter": "isDraft eq false",
            }
            if q:
                # Basic contains subject filter for MVP
                params["$search"] = q
            r = await self._request_with_retry(
                "GET",
                f"{self._base()}/me/messages",
                params=params,
                headers={"Authorization": f"Bearer {token}"},
                expected_status=[200],
            )
            if r.status_code == 401:
                raise ProviderError(
                    "microsoft",
                    "list_threads",
                    "unauthorized",
                    status_code=401,
                    hint="Reconnect Microsoft",
                )
            data = r.json()
            items = data.get("value", [])
            increment("ms.email.list_threads.ok", n=len(items))
            return [
                {
                    "id": it.get("id"),
                    "subject": it.get("subject"),
                    "from": (it.get("from") or {})
                    .get("emailAddress", {})
                    .get("address"),
                    "to": [
                        x.get("emailAddress", {}).get("address")
                        for x in (it.get("toRecipients") or [])
                    ],
                    "received_at": it.get("receivedDateTime"),
                    "preview": it.get("bodyPreview"),
                    "link": it.get("webLink"),
                }
                for it in items
            ]

        return anyio.run(_run)

    def list_inbox(self, limit: int = 5) -> List[Dict[str, Any]]:
        import anyio

        async def _run() -> List[Dict[str, Any]]:
            token = await self._auth()
            params = {
                "$top": str(max(1, min(limit or 5, 25))),
                "$select": "subject,from,toRecipients,receivedDateTime,bodyPreview,webLink",
                "$orderby": "receivedDateTime desc",
            }
            r = await self._request_with_retry(
                "GET",
                f"{self._base()}/me/messages",
                params=params,
                headers={"Authorization": f"Bearer {token}"},
                expected_status=[200],
            )
            if r.status_code == 401:
                raise ProviderError(
                    "microsoft",
                    "list_inbox",
                    "unauthorized",
                    status_code=401,
                    hint="Reconnect Microsoft",
                )
            data = r.json()
            items = data.get("value", [])
            increment("ms.email.inbox.listed", n=len(items))
            return [
                {
                    "id": it.get("id"),
                    "subject": it.get("subject"),
                    "from": (it.get("from") or {})
                    .get("emailAddress", {})
                    .get("address"),
                    "received_at": it.get("receivedDateTime"),
                    "preview": it.get("bodyPreview"),
                    "link": it.get("webLink"),
                }
                for it in items
            ]

        return anyio.run(_run)

    def create_draft(self, to: List[str], subject: str, body: str) -> Dict[str, Any]:
        import anyio

        async def _run() -> Dict[str, Any]:
            token = await self._auth()
            msg = {
                "subject": subject,
                "body": {"contentType": "Text", "content": body},
                "toRecipients": [{"emailAddress": {"address": t}} for t in to],
                "isDraft": True,
            }
            r = await self._request_with_retry(
                "POST",
                f"{self._base()}/me/messages",
                json=msg,
                headers={"Authorization": f"Bearer {token}"},
                expected_status=[201, 200],
            )
            data = r.json()
            increment("ms.email.create_draft.ok")
            return {
                "id": data.get("id"),
                "to": to,
                "subject": subject,
                "body": body,
                "status": "draft",
            }

        return anyio.run(_run)

    def send_draft(self, draft_id: str) -> Dict[str, Any]:
        import anyio

        async def _run() -> Dict[str, Any]:
            token = await self._auth()
            r = await self._request_with_retry(
                "POST",
                f"{self._base()}/me/messages/{draft_id}/send",
                headers={"Authorization": f"Bearer {token}"},
                expected_status=[202, 200, 204],
            )
            if r.status_code not in (202, 200, 204):
                raise ProviderError(
                    "microsoft", "send_draft", f"status={r.status_code}"
                )
            increment("ms.email.send_draft.ok")
            return {"id": draft_id, "status": "sent"}

        return anyio.run(_run)

    def send_message(self, to: List[str], subject: str, body: str) -> Dict[str, Any]:
        import anyio

        async def _run() -> Dict[str, Any]:
            token = await self._auth()
            payload = {
                "message": {
                    "subject": subject,
                    "body": {"contentType": "Text", "content": body},
                    "toRecipients": [{"emailAddress": {"address": t}} for t in to],
                }
            }
            r = await self._request_with_retry(
                "POST",
                f"{self._base()}/me/sendMail",
                json=payload,
                headers={"Authorization": f"Bearer {token}"},
                expected_status=[202, 200, 204],
            )
            if r.status_code not in (202, 200, 204):
                raise ProviderError(
                    "microsoft", "send_message", f"status={r.status_code}"
                )
            increment("ms.email.send_message.ok")
            return {"id": "send_mail", "status": "sent"}

        return anyio.run(_run)

    def get_message(self, message_id: str) -> Dict[str, Any]:
        import anyio

        async def _run() -> Dict[str, Any]:
            token = await self._auth()
            r = await self._request_with_retry(
                "GET",
                f"{self._base()}/me/messages/{message_id}",
                params={
                    "$select": "subject,from,toRecipients,receivedDateTime,bodyPreview,webLink"
                },
                headers={"Authorization": f"Bearer {token}"},
                expected_status=[200],
            )
            increment("ms.email.get_message.ok")
            return r.json()

        return anyio.run(_run)

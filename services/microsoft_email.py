from __future__ import annotations
from typing import Any, Dict, List
import os
import httpx

from services.providers.email_provider import EmailProvider
from services.providers.errors import ProviderError
from services.ms_auth import ensure_access_token


class MicrosoftEmailProvider(EmailProvider):
    def __init__(self, user_id: str, tenant_id: str | None = None) -> None:
        self.user_id = user_id
        self.tenant_id = tenant_id or os.getenv("MS_TENANT_ID", "common")

    def _base(self) -> str:
        return "https://graph.microsoft.com/v1.0"

    async def _auth(self) -> str:
        # For MVP, fetch from oauth_tokens via Supabase REST is external; assume middleware passes token elsewhere later
        # Here we require an access token via env for local smoke
        tok = os.getenv("MS_TEST_ACCESS_TOKEN", "")
        if not tok:
            raise ProviderError(
                "microsoft",
                "auth",
                "missing access token",
                hint="Set MS_TEST_ACCESS_TOKEN for local dev",
            )
        return tok

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
            async with httpx.AsyncClient(timeout=10) as c:
                r = await c.get(
                    f"{self._base()}/me/messages",
                    params=params,
                    headers={"Authorization": f"Bearer {token}"},
                )
                if r.status_code == 401:
                    raise ProviderError(
                        "microsoft",
                        "list_threads",
                        "unauthorized",
                        status_code=401,
                        hint="Reconnect Microsoft",
                    )
                r.raise_for_status()
                data = r.json()
                items = data.get("value", [])
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
            async with httpx.AsyncClient(timeout=10) as c:
                r = await c.post(
                    f"{self._base()}/me/messages",
                    json=msg,
                    headers={"Authorization": f"Bearer {token}"},
                )
                r.raise_for_status()
                data = r.json()
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
            async with httpx.AsyncClient(timeout=10) as c:
                r = await c.post(
                    f"{self._base()}/me/messages/{draft_id}/send",
                    headers={"Authorization": f"Bearer {token}"},
                )
                if r.status_code not in (202, 200, 204):
                    raise ProviderError(
                        "microsoft", "send_draft", f"status={r.status_code}"
                    )
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
            async with httpx.AsyncClient(timeout=10) as c:
                r = await c.post(
                    f"{self._base()}/me/sendMail",
                    json=payload,
                    headers={"Authorization": f"Bearer {token}"},
                )
                if r.status_code not in (202, 200, 204):
                    raise ProviderError(
                        "microsoft", "send_message", f"status={r.status_code}"
                    )
                return {"id": "send_mail", "status": "sent"}

        return anyio.run(_run)

    def get_message(self, message_id: str) -> Dict[str, Any]:
        import anyio

        async def _run() -> Dict[str, Any]:
            token = await self._auth()
            async with httpx.AsyncClient(timeout=10) as c:
                r = await c.get(
                    f"{self._base()}/me/messages/{message_id}",
                    params={
                        "$select": "subject,from,toRecipients,receivedDateTime,bodyPreview,webLink"
                    },
                    headers={"Authorization": f"Bearer {token}"},
                )
                r.raise_for_status()
                return r.json()

        return anyio.run(_run)

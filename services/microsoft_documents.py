"""Microsoft Graph Document provider."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
import os
import httpx
from datetime import datetime, timedelta, timezone

from services.providers.errors import ProviderError
from services.ms_auth import (
    ensure_access_token_sync,
    token_store_from_env,
    dev_get as _dev_token_get,
)
from utils.metrics import increment
from settings import GRAPH_TIMEOUT_MS, GRAPH_RETRY_MAX


class MicrosoftDocumentProvider:
    """Provider for Microsoft Graph document operations."""
    
    def __init__(self, user_id: str, tenant_id: str | None = None) -> None:
        self.user_id = user_id
        self.tenant_id = tenant_id or os.getenv("MS_TENANT_ID", "common")
    
    def _base(self) -> str:
        return "https://graph.microsoft.com/v1.0"
    
    async def _auth(self) -> str:
        """Get valid access token."""
        row = None
        try:
            store = token_store_from_env()
            row = store.get(self.user_id)
        except Exception:
            row = _dev_token_get(self.user_id)
        if not row:
            try:
                from presentation.api.routes import connections_msft as _cm  # type: ignore
                row = (_cm._DEV_TOKEN_STORE or {}).get(self.user_id)
            except Exception:
                row = None
        if row:
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
    
    async def list_recent_documents(
        self,
        days: int = 7,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """List recently modified documents from OneDrive and SharePoint.
        
        Returns list of documents with metadata.
        """
        token = await self._auth()
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        cutoff_str = cutoff.isoformat()
        
        documents = []
        
        # Get OneDrive recent files
        try:
            url = f"{self._base()}/me/drive/recent"
            params = {
                "$top": limit,
                "$filter": f"lastModifiedDateTime ge {cutoff_str}",
                "$select": "id,name,webUrl,lastModifiedDateTime,createdBy,lastModifiedBy,size",
            }
            
            async with httpx.AsyncClient(timeout=GRAPH_TIMEOUT_MS / 1000) as client:
                headers = {"Authorization": f"Bearer {token}"}
                response = await client.get(url, headers=headers, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    items = data.get("value", [])
                    
                    for item in items:
                        documents.append({
                            "id": item.get("id", ""),
                            "name": item.get("name", ""),
                            "web_url": item.get("webUrl", ""),
                            "last_modified": item.get("lastModifiedDateTime", ""),
                            "modified_by": item.get("lastModifiedBy", {}).get("user", {}).get("displayName", ""),
                            "source": "onedrive",
                            "type": "doc",
                        })
        except Exception:
            pass  # Continue even if OneDrive fails
        
        return documents
    
    async def get_document_changes(
        self,
        document_id: str,
        since: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get changes for a specific document.
        
        This is a stub - full implementation would use Graph API change tracking.
        """
        # For MVP, return mock change summary
        return {
            "document_id": document_id,
            "changes": [],
            "summary": "Document changes detected",
        }
    
    async def get_teams_messages(
        self,
        days: int = 7,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get recent Teams messages/mentions.
        
        Returns list of Teams messages that require attention.
        """
        token = await self._auth()
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        cutoff_str = cutoff.isoformat()
        
        messages = []
        
        # Get Teams chats with mentions
        try:
            url = f"{self._base()}/me/chats"
            params = {
                "$top": limit,
                "$expand": "lastMessagePreview",
            }
            
            async with httpx.AsyncClient(timeout=GRAPH_TIMEOUT_MS / 1000) as client:
                headers = {"Authorization": f"Bearer {token}"}
                response = await client.get(url, headers=headers, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    chats = data.get("value", [])
                    
                    for chat in chats:
                        preview = chat.get("lastMessagePreview", {})
                        if preview.get("isMentioned", False):
                            messages.append({
                                "id": chat.get("id", ""),
                                "subject": preview.get("body", {}).get("content", ""),
                                "from": preview.get("from", {}).get("user", {}).get("displayName", ""),
                                "timestamp": preview.get("createdDateTime", ""),
                                "web_url": f"https://teams.microsoft.com/l/chat/{chat.get('id', '')}",
                                "source": "teams",
                            })
        except Exception:
            pass  # Continue even if Teams fails
        
        return messages


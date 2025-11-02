"""Unified action items summary service."""
from __future__ import annotations
from typing import Any, Dict, List
from datetime import datetime, timezone
import uuid

from services.microsoft_documents import MicrosoftDocumentProvider
from services.microsoft_email import MicrosoftEmailProvider
from presentation.api.deps.providers import get_email_provider_for
from settings import USE_MOCK_GRAPH


async def generate_unified_action_items(
    user_id: str,
    days: int = 7,
) -> List[Dict[str, Any]]:
    """Generate unified action items from Outlook, Teams, and Docs.
    
    Aggregates action items from:
    - Email (needs response, needs approval)
    - Teams (mentions, unread messages)
    - Documents (recent changes, shared files)
    
    Returns list of ActionItem dicts.
    """
    action_items = []
    
    # 1. Get email action items
    try:
        email_provider = get_email_provider_for("list_inbox", user_id)
        if hasattr(email_provider, "list_inbox_async"):
            threads = await email_provider.list_inbox_async(limit=50)
        else:
            threads = email_provider.list_inbox(limit=50)
        
        for thread in threads[:20]:  # Limit to top 20
            # Determine category and priority
            category = "needs_response"  # Default
            priority = "medium"
            
            # Check for urgent keywords or senders
            subject = thread.get("subject", "").lower()
            if any(word in subject for word in ["urgent", "asap", "important"]):
                priority = "high"
            
            action_items.append({
                "action_id": str(uuid.uuid4()),
                "source": "email",
                "category": category,
                "priority": priority,
                "preview": thread.get("subject", "No subject"),
                "thread_id": thread.get("id"),
                "metadata": {
                    "from": thread.get("from", ""),
                    "received_at": thread.get("received_at", ""),
                },
            })
    except Exception:
        pass  # Continue if email fails
    
    # 2. Get Teams action items
    if not USE_MOCK_GRAPH:
        try:
            doc_provider = MicrosoftDocumentProvider(user_id)
            teams_messages = await doc_provider.get_teams_messages(days=days)
            
            for msg in teams_messages:
                action_items.append({
                    "action_id": str(uuid.uuid4()),
                    "source": "teams",
                    "category": "needs_response",
                    "priority": "high",  # Mentions are usually high priority
                    "preview": f"Mentioned in Teams: {msg.get('subject', '')[:100]}",
                    "metadata": {
                        "from": msg.get("from", ""),
                        "timestamp": msg.get("timestamp", ""),
                        "web_url": msg.get("web_url", ""),
                    },
                })
        except Exception:
            pass  # Continue if Teams fails
    
    # 3. Get document change action items
    if not USE_MOCK_GRAPH:
        try:
            doc_provider = MicrosoftDocumentProvider(user_id)
            documents = await doc_provider.list_recent_documents(days=days)
            
            # Group by document and create summary
            for doc in documents[:10]:  # Limit to top 10
                modified_by = doc.get("modified_by", "")
                if modified_by:  # Only if someone else modified it
                    action_items.append({
                        "action_id": str(uuid.uuid4()),
                        "source": "doc",
                        "category": "fyi",  # Document changes are usually FYI
                        "priority": "low",
                        "preview": f"Document updated: {doc.get('name', '')} by {modified_by}",
                        "metadata": {
                            "document_id": doc.get("id", ""),
                            "web_url": doc.get("web_url", ""),
                            "last_modified": doc.get("last_modified", ""),
                        },
                    })
        except Exception:
            pass  # Continue if docs fail
    
    # Sort by priority (high first) and source order (email > teams > doc)
    priority_order = {"high": 0, "medium": 1, "low": 2}
    source_order = {"email": 0, "teams": 1, "doc": 2}
    
    action_items.sort(
        key=lambda x: (
            priority_order.get(x.get("priority", "medium"), 1),
            source_order.get(x.get("source", "doc"), 2),
        )
    )
    
    return action_items


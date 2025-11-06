"""Notion helper utilities for querying and updating Notion databases.

This module provides functions to:
- Query Notion databases (via MCP server or direct API)
- Create, update, and find items in Notion databases
- Update page status and properties
- Find items by name or other criteria

Use this module programmatically from Cursor or import it in scripts.
"""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import httpx

# Load environment variables
try:
    from dotenv import load_dotenv
    try:
        load_dotenv(".env.local", override=True)
    except Exception:
        pass
    load_dotenv()
except Exception:
    pass

NOTION_TOKEN = os.getenv("NOTION_TOKEN") or os.getenv("NOTION_API_KEY", "")
NOTION_TASKS_DB_ID = os.getenv("NOTION_TASKS_DB_ID", "")
NOTION_PROJECTS_DB_ID = os.getenv("NOTION_PROJECTS_DB_ID", "")

NOTION_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"

# Database IDs (fallback to env if not provided)
DATABASES = {
    "tasks": NOTION_TASKS_DB_ID or "29f795383d90808f874ef7a8e7857c01",
    "projects": NOTION_PROJECTS_DB_ID or "29f795383d9080388644f9c25bdf2689",
}


def _headers() -> Dict[str, str]:
    """Get Notion API headers."""
    if not NOTION_TOKEN:
        raise ValueError("NOTION_TOKEN or NOTION_API_KEY environment variable not set")
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def get_database_id(database_type: str) -> str:
    """Get database ID for a given type (tasks or projects)."""
    db_type = database_type.lower()
    if db_type not in DATABASES:
        raise ValueError(f"Unknown database type: {database_type}. Must be 'tasks' or 'projects'")
    return DATABASES[db_type]


def find_item_by_name(
    database_id: str,
    item_name: str,
    name_property: str = "Name"
) -> Optional[Dict[str, Any]]:
    """Find a Notion page by name in a database.
    
    Args:
        database_id: The Notion database ID
        item_name: The name/title to search for (partial match)
        name_property: The property name that contains the title (default: "Name")
    
    Returns:
        The first matching page dict, or None if not found
    """
    with httpx.Client(timeout=10.0) as client:
        resp = client.post(
            f"{NOTION_BASE}/databases/{database_id}/query",
            headers=_headers(),
            json={
                "filter": {
                    "property": name_property,
                    "title": {"contains": item_name}
                }
            },
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        return results[0] if results else None


def query_database(
    database_id: str,
    filter_dict: Optional[Dict[str, Any]] = None,
    page_size: int = 100
) -> List[Dict[str, Any]]:
    """Query a Notion database with optional filters.
    
    Args:
        database_id: The Notion database ID
        filter_dict: Optional filter dictionary (Notion filter format)
        page_size: Number of results to return (max 100)
    
    Returns:
        List of page dictionaries
    """
    with httpx.Client(timeout=10.0) as client:
        payload = {"page_size": min(page_size, 100)}
        if filter_dict:
            payload["filter"] = filter_dict
        
        resp = client.post(
            f"{NOTION_BASE}/databases/{database_id}/query",
            headers=_headers(),
            json=payload,
        )
        resp.raise_for_status()
        return resp.json().get("results", [])


def update_page_status(
    page_id: str,
    status_name: str,
    status_property: str = "Status"
) -> Dict[str, Any]:
    """Update a page's status property.
    
    Args:
        page_id: The Notion page ID
        status_name: The status name (e.g., "In progress", "Done", "Not started")
        status_property: The property name for status (default: "Status")
    
    Returns:
        Updated page dictionary
    """
    with httpx.Client(timeout=10.0) as client:
        resp = client.patch(
            f"{NOTION_BASE}/pages/{page_id}",
            headers=_headers(),
            json={
                "properties": {
                    status_property: {
                        "status": {"name": status_name}
                    }
                }
            },
        )
        resp.raise_for_status()
        return resp.json()


def update_page_property(
    page_id: str,
    property_name: str,
    property_value: Dict[str, Any]
) -> Dict[str, Any]:
    """Update any property on a Notion page.
    
    Args:
        page_id: The Notion page ID
        property_name: The property name to update
        property_value: The property value (must match Notion API format)
    
    Returns:
        Updated page dictionary
    
    Example:
        update_page_property(page_id, "Priority", {"select": {"name": "High"}})
    """
    with httpx.Client(timeout=10.0) as client:
        resp = client.patch(
            f"{NOTION_BASE}/pages/{page_id}",
            headers=_headers(),
            json={
                "properties": {
                    property_name: property_value
                }
            },
        )
        resp.raise_for_status()
        return resp.json()


def get_items_by_status(
    database_type: str,
    status_name: str,
    status_property: str = "Status"
) -> List[Dict[str, Any]]:
    """Get all items in a database with a specific status.
    
    Args:
        database_type: "tasks" or "projects"
        status_name: Status name to filter by
        status_property: Property name for status (default: "Status")
    
    Returns:
        List of page dictionaries
    """
    database_id = get_database_id(database_type)
    filter_dict = {
        "property": status_property,
        "status": {"equals": status_name}
    }
    return query_database(database_id, filter_dict)


def update_item_status(
    database_type: str,
    item_name: str,
    new_status: str,
    name_property: str = "Name",
    status_property: str = "Status"
) -> Dict[str, Any]:
    """Find an item by name and update its status.
    
    Args:
        database_type: "tasks" or "projects"
        item_name: Name of the item to update
        new_status: New status value
        name_property: Property name for item name (default: "Name")
        status_property: Property name for status (default: "Status")
    
    Returns:
        Updated page dictionary
    
    Raises:
        ValueError: If item not found
    """
    database_id = get_database_id(database_type)
    item = find_item_by_name(database_id, item_name, name_property)
    
    if not item:
        raise ValueError(f"Item '{item_name}' not found in {database_type} database")
    
    page_id = item["id"]
    return update_page_status(page_id, new_status, status_property)


def create_task(
    title: str,
    project_id: str,
    notes: str = "",
    database_type: str = "tasks"
) -> Dict[str, Any]:
    """Create a new task in Notion.
    
    Args:
        title: Task title/name
        project_id: Notion project page ID to link the task to
        notes: Optional notes/description for the task
        database_type: Database type to create in (default: "tasks")
    
    Returns:
        Created page dictionary from Notion API
    
    Raises:
        ValueError: If database_type is invalid or token not set
    """
    database_id = get_database_id(database_type)
    
    properties = {
        "Name": {"title": [{"text": {"content": title}}]},
        "Status": {"status": {"name": "Not started"}},
        "Project": {"relation": [{"id": project_id}]},
    }
    
    if notes:
        properties["Notes"] = {"rich_text": [{"text": {"content": notes}}]}
    
    with httpx.Client(timeout=10.0) as client:
        resp = client.post(
            f"{NOTION_BASE}/pages",
            headers=_headers(),
            json={
                "parent": {"database_id": database_id},
                "properties": properties
            },
        )
        resp.raise_for_status()
        return resp.json()


def get_page_content(page_id: str) -> Dict[str, Any]:
    """Retrieve a Notion page with all its properties.
    
    Args:
        page_id: The Notion page ID
    
    Returns:
        Page dictionary with properties
    """
    with httpx.Client(timeout=10.0) as client:
        resp = client.get(
            f"{NOTION_BASE}/pages/{page_id}",
            headers=_headers(),
        )
        resp.raise_for_status()
        return resp.json()


"""Mock database layer for LLM testing.

Provides in-memory storage that mimics Supabase behavior for testing.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
import uuid
from datetime import datetime, timezone


class MockSupabaseClient:
    """In-memory mock of Supabase REST API client."""

    def __init__(self):
        self._tables: Dict[str, List[Dict[str, Any]]] = {
            "users": [],
            "projects": [],
            "tasks": [],
            "threads": [],
            "messages": [],
            "action_items": [],
            "task_action_links": [],
            "task_sources": [],
        }
        self._next_id = 1
        self._seed_default_user()

    def _seed_default_user(self):
        """Seed a default user for testing."""
        default_user = {
            "id": "ea7f6212-c420-4be5-84e3-c34257b4fa99",
            "tenant_id": "6b58b8eb-70a0-4efd-8354-c5cf0862d983",
            "email": "test.user+local@example.com",
            "name": "Test User",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        self._tables["users"].append(default_user)

    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> MockResponse:
        """Mock GET request."""
        table = path.lstrip("/")
        filters = params or {}

        # Get all rows for table
        rows = self._tables.get(table, [])

        # Apply filters
        limit_applied = False
        for key, value in filters.items():
            if key == "select":
                continue  # Ignore select for now
            if key == "order":
                # Simple ordering - just reverse if desc
                if "desc" in str(value):
                    rows = list(reversed(rows))
                continue
            if key == "limit":
                limit = int(value)
                rows = rows[:limit]
                limit_applied = True
                continue

            # Parse filter (e.g., "tenant_id": "eq.123")
            if "." in str(value):
                op, val = str(value).split(".", 1)
                if op == "eq":
                    rows = [r for r in rows if str(r.get(key)) == val]
                elif op == "neq":
                    rows = [r for r in rows if str(r.get(key)) != val]
                elif op == "is":
                    # Handle "is.null" and "is.not.null"
                    if val == "null":
                        rows = [r for r in rows if r.get(key) is None]
                    elif val == "not.null":
                        rows = [r for r in rows if r.get(key) is not None]

        # Apply limit after filtering if not already applied
        if not limit_applied and "limit" in filters:
            limit = int(filters["limit"])
            rows = rows[:limit]

        return MockResponse(200, rows)

    def post(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None,
    ) -> MockResponse:
        """Mock POST request (insert)."""
        table = path.lstrip("/")
        if table not in self._tables:
            return MockResponse(404, {"error": "Table not found"})

        payload = json or {}
        # Generate ID if not provided
        if "id" not in payload:
            payload["id"] = str(uuid.uuid4())
        if "created_at" not in payload:
            payload["created_at"] = datetime.now(timezone.utc).isoformat()
        if "updated_at" not in payload:
            payload["updated_at"] = datetime.now(timezone.utc).isoformat()

        self._tables[table].append(payload.copy())

        # Return representation if requested
        if headers and headers.get("Prefer") == "return=representation":
            return MockResponse(201, payload)
        return MockResponse(201, payload)

    def patch(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None,
    ) -> MockResponse:
        """Mock PATCH request (update)."""
        table = path.lstrip("/")
        if table not in self._tables:
            return MockResponse(404, {"error": "Table not found"})

        # Find matching rows
        filters = params or {}
        rows = self._tables[table]
        matching_indices = []

        for key, value in filters.items():
            if "." in str(value):
                op, val = str(value).split(".", 1)
                if op == "eq":
                    for i, row in enumerate(rows):
                        if str(row.get(key)) == val:
                            matching_indices.append(i)

        if not matching_indices:
            return MockResponse(404, {"error": "Not found"})

        # Update all matching rows (for batch updates)
        updated_rows = []
        for idx in matching_indices:
            update_data = json or {}
            # Handle setting deleted_at to None explicitly
            if "deleted_at" in update_data and update_data["deleted_at"] is None:
                rows[idx]["deleted_at"] = None
            else:
                rows[idx].update(update_data)
            rows[idx]["updated_at"] = datetime.now(timezone.utc).isoformat()
            updated_rows.append(rows[idx])

        if headers and headers.get("Prefer") == "return=representation":
            # Return as list for consistency with Supabase
            return MockResponse(200, updated_rows if len(updated_rows) > 1 else [updated_rows[0]] if updated_rows else [])
        return MockResponse(200, updated_rows[0] if updated_rows else None)

    def delete(
        self, path: str, params: Optional[Dict[str, Any]] = None
    ) -> MockResponse:
        """Mock DELETE request."""
        table = path.lstrip("/")
        if table not in self._tables:
            return MockResponse(404, {"error": "Table not found"})

        filters = params or {}
        rows = self._tables[table]
        to_remove = []

        for key, value in filters.items():
            if "." in str(value):
                op, val = str(value).split(".", 1)
                if op == "eq":
                    for i, row in enumerate(rows):
                        if row.get(key) == val:
                            to_remove.append(i)

        # Remove in reverse order to maintain indices
        for i in sorted(to_remove, reverse=True):
            rows.pop(i)

        return MockResponse(204, None)

    def clear(self):
        """Clear all tables except users."""
        default_user = self._tables["users"][0] if self._tables.get("users") else None
        for table in self._tables:
            self._tables[table].clear()
        # Re-seed default user
        if default_user:
            self._tables["users"].append(default_user)
        else:
            self._seed_default_user()

    def seed_workroom(self, user_id: str, tenant_id: str) -> Dict[str, Any]:
        """Seed workroom with test data."""
        # Preserve action_items when seeding workroom (they may have been seeded separately)
        preserved_action_items = self._tables.get("action_items", [])[:]
        self.clear()
        self._tables["action_items"] = preserved_action_items

        # Create projects
        project1 = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "owner_id": user_id,
            "name": "Product Launch",
            "description": "Q4 product launch planning and execution",
            "status": "active",
            "priority": "medium",
            "order_index": 0,
            "metadata": {},
            "deleted_at": None,
        }
        project2 = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "owner_id": user_id,
            "name": "Marketing Campaign",
            "description": "Social media and email marketing campaign",
            "status": "active",
            "priority": "medium",
            "order_index": 1,
            "metadata": {},
            "deleted_at": None,
        }
        self._tables["projects"].extend([project1, project2])

        # Create tasks
        task1 = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "project_id": project1["id"],
            "owner_id": user_id,
            "title": "Design landing page",
            "status": "doing",
            "priority": "high",
            "order_index": 0,
            "source_type": "manual",
            "source_ref": {},
            "deleted_at": None,
        }
        task2 = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "project_id": project1["id"],
            "owner_id": user_id,
            "title": "Write product copy",
            "status": "ready",
            "priority": "medium",
            "order_index": 1,
            "source_type": "manual",
            "source_ref": {},
            "deleted_at": None,
        }
        self._tables["tasks"].extend([task1, task2])

        return {
            "projects": [project1, project2],
            "tasks": [task1, task2],
        }

    def seed_queue(
        self, user_id: str, tenant_id: str, count: int = 5
    ) -> List[Dict[str, Any]]:
        """Seed queue with test action items."""
        items = []
        priorities = ["high", "medium", "low"]
        sources = ["email", "teams", "doc"]
        for i in range(count):
            item = {
                "id": str(uuid.uuid4()),
                "tenant_id": tenant_id,
                "owner_id": user_id,
                "source_type": sources[i % len(sources)],
                "source_id": f"msg-{i}",
                "priority": priorities[i % len(priorities)],
                "state": "queued",
                "payload": {
                    "preview": f"Test action item {i+1}: Follow up on Q4 planning meeting",
                    "subject": f"Test Email {i+1}",
                },
            }
            items.append(item)
            self._tables["action_items"].append(item)
        return items


class MockResponse:
    """Mock HTTP response."""

    def __init__(self, status_code: int, data: Any):
        self.status_code = status_code
        self._data = data

    def json(self) -> Any:
        return self._data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


# Global mock client instance
_mock_client: Optional[MockSupabaseClient] = None


def get_mock_client() -> MockSupabaseClient:
    """Get or create the global mock client."""
    global _mock_client
    if _mock_client is None:
        _mock_client = MockSupabaseClient()
    return _mock_client


def reset_mock_db():
    """Reset the mock database."""
    global _mock_client
    if _mock_client:
        _mock_client.clear()
    else:
        _mock_client = MockSupabaseClient()

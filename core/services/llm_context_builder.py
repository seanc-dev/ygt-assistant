"""LLM Context Builder for operations protocol.

Builds compact context views of user's projects, tasks, and action items
for LLM operations. Designed to support both "full" and "summarised" modes
for cost optimization (summarised mode is future work).
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def build_context_for_user(
    tenant_id: str,
    user_id: str,
    *,
    max_projects: int = 20,
    max_tasks: int = 50,
    max_actions: int = 20,
    focus_action_id: Optional[str] = None,
    focus_task_id: Optional[str] = None,
    summary_mode: bool = False,
) -> Dict[str, Any]:
    """Build context for LLM operations.
    
    Args:
        tenant_id: Tenant identifier
        user_id: User identifier
        max_projects: Maximum projects to include
        max_tasks: Maximum tasks to include
        max_actions: Maximum action items to include
        focus_action_id: Optional action ID to focus on
        focus_task_id: Optional task ID to focus on
        summary_mode: If True, return summarised context (future: for cost optimization)
    
    Returns:
        Context dict with projects, tasks, actions, and focus_item if applicable
    """
    from presentation.api.repos import workroom, queue, tasks
    
    context: Dict[str, Any] = {
        "projects": [],
        "tasks": [],
        "actions": [],
        "focus_item": None,
    }
    
    try:
        # Load projects
        projects = workroom.get_projects(user_id)
        context["projects"] = [
            {
                "id": p["id"],
                "name": p.get("name", ""),
                "description": p.get("description"),
                "status": p.get("status", "active"),
            }
            for p in projects[:max_projects]
        ]
    except Exception as e:
        logger.warning(f"Failed to load projects: {e}")
    
    try:
        # Load tasks
        all_tasks = workroom.get_tasks(user_id)
        context["tasks"] = [
            {
                "id": t["id"],
                "title": t.get("title", ""),
                "description": t.get("description"),
                "status": t.get("status", "backlog"),
                "priority": t.get("priority", "medium"),
                "project_id": t.get("project_id"),
            }
            for t in all_tasks[:max_tasks]
        ]
    except Exception as e:
        logger.warning(f"Failed to load tasks: {e}")
    
    try:
        # Load action items (queue)
        action_items = queue.get_queue_items(user_id, limit=max_actions)
        context["actions"] = [
            {
                "id": a["id"],
                "source_type": a.get("source_type", "manual"),
                "source_id": a.get("source_id"),
                "priority": a.get("priority", "medium"),
                "state": a.get("state", "queued"),
                "preview": a.get("payload", {}).get("preview") or a.get("payload", {}).get("subject", ""),
                "task_id": a.get("task_id"),
            }
            for a in action_items[:max_actions]
        ]
    except Exception as e:
        logger.warning(f"Failed to load action items: {e}")
    
    # Set focus item if provided
    if focus_action_id:
        try:
            action = tasks.get_action_item(user_id, focus_action_id)
            context["focus_item"] = {
                "type": "action",
                "id": action["id"],
                "source_type": action.get("source_type", "manual"),
                "priority": action.get("priority", "medium"),
                "state": action.get("state", "queued"),
                "payload": action.get("payload", {}),
            }
        except Exception as e:
            logger.warning(f"Failed to load focus action: {e}")
    
    elif focus_task_id:
        try:
            task = workroom.get_task(user_id, focus_task_id)
            context["focus_item"] = {
                "type": "task",
                "id": task["id"],
                "title": task.get("title", ""),
                "status": task.get("status", "backlog"),
                "priority": task.get("priority", "medium"),
            }
        except Exception as e:
            logger.warning(f"Failed to load focus task: {e}")
    
    # TODO: When summary_mode=True, replace full objects with summaries
    # This will reduce token usage for cost optimization
    # Example: replace full task objects with {id, title, status} only
    
    return context


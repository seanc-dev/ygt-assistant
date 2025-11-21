from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


def _truncate_list(items: List[Dict[str, Any]], limit: int) -> Tuple[List[Dict[str, Any]], int]:
    """Return a truncated list and the number of omitted items."""

    if limit <= 0:
        return [], len(items)

    visible = items[:limit]
    omitted = max(len(items) - limit, 0)
    return visible, omitted


@dataclass
class WorkroomContextSpace:
    """Structured, truncated Workroom context sent to the LLM."""

    anchor_task_id: Optional[str]
    anchor_project_id: Optional[str]
    projects: List[Dict[str, Any]]
    tasks: List[Dict[str, Any]]
    actions: List[Dict[str, Any]]
    truncated: Dict[str, int]

    def to_context_input(self) -> Dict[str, Any]:
        """Convert to the contract-friendly context_input payload."""

        payload: Dict[str, Any] = {
            "anchor": {
                "task_id": self.anchor_task_id,
                "project_id": self.anchor_project_id,
            }
        }

        if self.projects:
            payload["projects"] = self.projects
        if self.tasks:
            payload["tasks"] = self.tasks
        if self.actions:
            payload["actions"] = self.actions

        truncated_fields = {k: v for k, v in self.truncated.items() if v > 0}
        if truncated_fields:
            payload["truncated"] = truncated_fields

        return payload


def build_workroom_context_space(
    context: Optional[Dict[str, Any]],
    *,
    focus_task_id: Optional[str] = None,
    focus_project_id: Optional[str] = None,
    max_projects: int = 8,
    max_tasks: int = 12,
    max_actions: int = 8,
) -> Optional[WorkroomContextSpace]:
    """Create a truncated WorkroomContextSpace from the broader context payload."""

    context = context or {}
    projects = context.get("projects") or []
    tasks = context.get("tasks") or []
    actions = context.get("actions") or []

    anchor_task_id = focus_task_id
    anchor_project_id = focus_project_id

    if not anchor_project_id and focus_task_id:
        focus_task = next((t for t in tasks if t.get("id") == focus_task_id), None)
        if focus_task:
            anchor_project_id = focus_task.get("project_id")

    project_payload, omitted_projects = _truncate_list(
        [
            {
                "id": project.get("id"),
                "name": project.get("name"),
                "status": project.get("status"),
            }
            for project in projects
            if project.get("id")
        ],
        max_projects,
    )

    task_payload, omitted_tasks = _truncate_list(
        [
            {
                "id": task.get("id"),
                "title": task.get("title"),
                "status": task.get("status"),
                "project_id": task.get("project_id"),
            }
            for task in tasks
            if task.get("id")
        ],
        max_tasks,
    )

    action_payload, omitted_actions = _truncate_list(
        [
            {
                "id": action.get("id"),
                "preview": action.get("preview")
                or action.get("title")
                or action.get("payload", {}).get("preview")
                or action.get("payload", {}).get("subject"),
                "source_type": action.get("source_type"),
            }
            for action in actions
            if action.get("id")
        ],
        max_actions,
    )

    if not (project_payload or task_payload or action_payload or anchor_task_id or anchor_project_id):
        return None

    return WorkroomContextSpace(
        anchor_task_id=anchor_task_id,
        anchor_project_id=anchor_project_id,
        projects=project_payload,
        tasks=task_payload,
        actions=action_payload,
        truncated={
            "projects": omitted_projects,
            "tasks": omitted_tasks,
            "actions": omitted_actions,
        },
    )


__all__ = [
    "WorkroomContextSpace",
    "build_workroom_context_space",
]

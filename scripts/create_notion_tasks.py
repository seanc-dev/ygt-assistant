#!/usr/bin/env python3
"""
CLI script for creating Notion tasks.

Usage:
    # Create tasks from Python list (for programmatic use)
    python scripts/create_notion_tasks.py

    # Import and use in code (preferred):
    from utils.notion_helper import create_task
    create_task("Task title", "project_id", "Optional notes")

Examples:
    # Create a single task programmatically
    python scripts/create_notion_tasks.py

    # Import and use in code (preferred):
    from utils.notion_helper import create_task
    create_task("My task", "project-id-here", "Task description")
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.notion_helper import create_task


def main():
    """Create LLM ops protocol backlog tasks."""
    # LLM Ops Protocol backlog tasks
    tasks = [
        {
            "title": "Support multi-task linking from a single action (schema + UI + LLM behaviour)",
            "tags": ["LLM Ops", "Schema", "UI"],
            "priority": "Medium",
            "notes": "Extend task_action_links and task_sources to support multiple tasks per action. Update UI to allow multi-select and LLM to propose multiple task links.",
        },
        {
            "title": "Robust JSON-only fallback for LLM operations (parsing + tests)",
            "tags": ["LLM Ops", "Testing"],
            "priority": "High",
            "notes": "Enhance JSON extraction to handle edge cases: nested code fences, multiple JSON objects, partial JSON recovery. Add comprehensive test coverage.",
        },
        {
            "title": "Context builder must support swap between full context and summarised context (for cost optimisation)",
            "tags": ["LLM Ops", "Cost Optimization"],
            "priority": "High",
            "notes": "The context builder in core/services/llm_context_builder.py currently has a summary_mode parameter stub. Implement summarised mode that returns compact views (id, title, status only) instead of full objects to reduce token usage.",
        },
        {
            "title": "Fine-grained trust rules by surface and recipient type (Queue vs Workroom, internal vs external, team vs wider org)",
            "tags": ["LLM Ops", "Trust Gating"],
            "priority": "Medium",
            "notes": "Extend trust gating beyond simple mode-based rules. Add context-aware risk assessment based on: surface (Queue vs Workroom), recipient type (internal vs external), and org scope (team vs wider org).",
        },
        {
            "title": "Contextual history surfaces (task/queue/today) backed by audit_log; global history deprioritised",
            "tags": ["History", "UI"],
            "priority": "Low",
            "notes": "Build contextual history views for tasks, queue items, and today's activities using audit_log. Deprioritise global history page expansion in favor of these contextual views.",
        },
    ]

    for task in tasks:
        try:
            create_task(
                title=task["title"],
                project_id=None,  # No project link for these tasks
                notes=task["notes"],
                priority=task["priority"],
                tags=task["tags"],
            )
            print(f"✓ Created: {task['title']}")
        except Exception as e:
            print(f"✗ Error creating '{task['title']}': {e}")


if __name__ == "__main__":
    main()

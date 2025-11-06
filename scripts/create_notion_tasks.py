#!/usr/bin/env python3
"""
CLI script for creating Notion tasks.

Usage:
    # Create tasks from Python list (for programmatic use)
    python scripts/create_notion_tasks.py

    # Or use as a module:
    from scripts.create_notion_tasks import create_task

    create_task("Task title", "project_id", "Optional notes")

Examples:
    # Create a single task programmatically
    python scripts/create_notion_tasks.py

    # Import and use in code
    from scripts.create_notion_tasks import create_task
    create_task("My task", "project-id-here", "Task description")
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.notion_helper import create_task as create_task_helper


def create_task(title, project_id, notes=""):
    """Create a task in Notion.

    Convenience wrapper around utils.notion_helper.create_task.
    Kept for backward compatibility and simpler import path.

    Args:
        title: Task title/name
        project_id: Notion project page ID to link the task to
        notes: Optional notes/description for the task

    Returns:
        Created page dictionary from Notion API
    """
    return create_task_helper(title, project_id, notes)


def main():
    """Example usage - can be customized for specific use cases."""
    # Schedule Alternatives project ID
    project_id = "29f79538-3d90-80e2-926e-f4582cdea037"

    # Example tasks (customize as needed)
    tasks = [
        (
            "Build smart command flow with approval/edit/decline",
            project_id,
            "Add a way for users to approve/edit/decline the LLM's interpretation of their command before it's implemented.",
        ),
        (
            "Implement schedule block types with colors",
            project_id,
            "Add different colors for meetings vs work vs external vs personal, or whichever categories we decide to include.",
        ),
        (
            "Define schedule items relationship to tasks/threads",
            project_id,
            "Decide on how schedule items relate to tasks/threads. Could be they relate to a thread themselves, which is what workroom opens when Open in Workroom is clicked. Whatever is decided this needs to be implemented.",
        ),
    ]

    for title, pid, notes in tasks:
        try:
            create_task(title, pid, notes)
            print(f"✓ Created: {title}")
        except Exception as e:
            print(f"✗ Error creating '{title}': {e}")


if __name__ == "__main__":
    main()

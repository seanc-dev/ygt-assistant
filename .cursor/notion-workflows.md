# Notion Workflow Guide for Cursor

This guide helps you work with Notion databases as your project management store within Cursor.

## Overview

- **MCP Server**: Use for querying/searching databases (read-only works well)
- **Direct API**: Use for updates (via `utils/notion_helper.py` or `scripts/notion_update.py`)

## Database IDs

- **Tasks**: `29f795383d90808f874ef7a8e7857c01`
- **Projects**: `29f795383d9080388644f9c25bdf2689`

## Common Workflows

### 1. Update Task/Project Status

**Prompt Examples:**
```
Update the task "[task name]" to "Done" status
Update the project "[project name]" to "In progress" status
Mark "[item name]" as completed in [tasks|projects]
```

**How to implement:**
- Use `utils.notion_helper.update_item_status()` in Python code
- Or call `scripts/notion_update.py` from terminal
- Or use direct API calls via curl/Python

**Example Python:**
```python
from utils.notion_helper import update_item_status

# Update a task
update_item_status("tasks", "Create route stubs", "Done")

# Update a project
update_item_status("projects", "Hub Queue", "In progress")
```

### 2. Query Database for Context

**Prompt Examples:**
```
Show me all tasks with status "In progress"
What projects are currently "Not started"?
Find all items in the Tasks database that need attention
Pull context from Notion: show me tasks related to [keyword]
```

**How to implement:**
- Use MCP server: `mcp_notion_API-post-database-query`
- Or use `utils.notion_helper.get_items_by_status()`
- Or use `utils.notion_helper.query_database()`

**Example Python:**
```python
from utils.notion_helper import get_items_by_status, query_database

# Get all in-progress tasks
tasks = get_items_by_status("tasks", "In progress")

# Query with custom filter
items = query_database(
    database_id,
    filter_dict={"property": "Tags", "multi_select": {"contains": "api"}}
)
```

### 3. Review Database for Next Steps

**Prompt Examples:**
```
Review the Tasks database and identify what needs to be done next
Show me tasks that are "Not started" and have high priority
What are the next 3 items I should focus on?
Pull context from Notion for planning today's work
```

**How to implement:**
- Query multiple statuses and priorities
- Combine filters to find actionable items
- Present results in a clear format

**Example Python:**
```python
from utils.notion_helper import get_items_by_status, get_database_id, query_database

# Get not-started high-priority tasks
db_id = get_database_id("tasks")
not_started = query_database(
    db_id,
    filter_dict={
        "and": [
            {"property": "Status", "status": {"equals": "Not started"}},
            {"property": "Priority", "select": {"equals": "High"}}
        ]
    }
)
```

### 4. Update Item with Text

**Prompt Examples:**
```
Add the following text to the Notes field of task "[task name]": [update text]
Update the Notes field for project "[project name]" with: [update text]
Append "[text]" to the Notes field of task "[task name]"
```

**How to implement:**
- Use `update_page_property()` to update rich_text fields
- Use `find_item_by_name()` to locate the item
- Use `get_page_content()` to retrieve existing content for appending

**Example Python:**
```python
from utils.notion_helper import find_item_by_name, update_page_property, get_page_content, get_database_id

# Add text to Notes field (replaces existing)
task = find_item_by_name(get_database_id("tasks"), "Task name")
if task:
    update_page_property(
        task["id"],
        "Notes",
        {"rich_text": [{"text": {"content": "Your update text here"}}]}
    )

# Append to existing Notes (retrieve first, then append)
task = find_item_by_name(get_database_id("tasks"), "Task name")
if task:
    content = get_page_content(task["id"])
    existing_notes = content["properties"].get("Notes", {}).get("rich_text", [])
    existing_text = existing_notes[0]["plain_text"] if existing_notes else ""
    new_text = existing_text + "\n\n[New update text]"
    update_page_property(
        task["id"],
        "Notes",
        {"rich_text": [{"text": {"content": new_text}}]}
    )
```

## Status Values

**Tasks:**
- "Not started"
- "In progress"
- "Done"

**Projects:**
- "Not started"
- "In progress"
- "Done"

## Quick Reference Commands

```bash
# Update task status
python scripts/notion_update.py tasks "Task name" "Done"

# Update project status
python scripts/notion_update.py projects "Project name" "In progress"

# List items with status
python scripts/notion_update.py tasks --list "In progress"
python scripts/notion_update.py projects --list "Not started"
```

## Integration Tips

1. **Use MCP for queries**: The MCP server works great for searching and reading. Use it when you need to find items or pull context.

2. **Use API for updates**: Direct API calls are more reliable for updates. Use `utils/notion_helper.py` functions or the CLI script.

3. **Update text fields**: Use `update_page_property()` with rich_text format to add or update Notes fields.

4. **Combine workflows**: Query databases for context, then update items based on completion or changes.

5. **Error handling**: Always check if items exist before updating. The helper functions raise `ValueError` if items aren't found.

## Example: Complete Workflow

```python
from utils.notion_helper import (
    get_items_by_status,
    update_item_status,
    find_item_by_name,
    get_page_content
)

# 1. Review what's in progress
in_progress_tasks = get_items_by_status("tasks", "In progress")
print(f"Found {len(in_progress_tasks)} tasks in progress")

# 2. Mark completed items as Done
for task in in_progress_tasks:
    name = task["properties"]["Name"]["title"][0]["plain_text"]
    # Check if completed (logic here)
    if is_completed(task):
        update_item_status("tasks", name, "Done")

# 3. Find next items to work on
not_started = get_items_by_status("tasks", "Not started")
priority_items = [t for t in not_started if is_high_priority(t)]

# 4. Add updates to items
for item in priority_items:
    name = item["properties"]["Name"]["title"][0]["plain_text"]
    update_page_property(
        item["id"],
        "Notes",
        {"rich_text": [{"text": {"content": f"Review notes for {name}"}}]}
    )

## Troubleshooting

- **Authentication errors**: Ensure `NOTION_TOKEN` is set in `.env.local`
- **Item not found**: Check exact spelling/capitalization of item names
- **Status value errors**: Use exact status names: "Not started", "In progress", "Done"
- **MCP server issues**: Use direct API calls via `utils/notion_helper.py` as fallback


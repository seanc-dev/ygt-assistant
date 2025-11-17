# Notion Integration Setup - Complete ✅

## What Was Created

1. **`utils/notion_helper.py`** - Python module for programmatic Notion operations (queries and updates)
2. **`scripts/notion_update.py`** - CLI script for updating Notion items
3. **`.cursor/notion-workflows.md`** - Comprehensive workflow guide
4. **`.cursor/notion-prompts.md`** - Quick reference prompts

## How to Use

### Quick Updates (CLI)
```bash
# Update a task to Done
python scripts/notion_update.py tasks "Task name" "Done"

# Update a project to In progress
python scripts/notion_update.py projects "Project name" "In progress"

# List items with status
python scripts/notion_update.py tasks --list "In progress"
```

### In Python/Cursor
```python
from utils.notion_helper import (
    update_item_status, 
    get_items_by_status,
    query_database,
    find_item_by_name,
    get_page_content
)

# Update status
update_item_status("tasks", "Task name", "Done")

# Query database by status
tasks = get_items_by_status("tasks", "In progress")

# Query with custom filters
db_id = get_database_id("tasks")
items = query_database(db_id, {"property": "Status", "status": {"equals": "In progress"}})

# Find item by name
task = find_item_by_name(get_database_id("tasks"), "Task name")

# Get page content
content = get_page_content(page_id)
```

### Using Notion API (for all operations)
Use `utils.notion_helper` functions for reading/searching:
- `query_database(database_id, filter_dict)` - Query databases with filters
- `get_items_by_status(database_type, status_name)` - Get items by status
- `find_item_by_name(database_id, item_name)` - Find items by name
- `get_page_content(page_id)` - Get page properties and content
- `get_database_id(database_type)` - Get database ID

## Configuration

- **API Access**: Use `utils/notion_helper.py` or `scripts/notion_update.py` for all operations
- **Environment**: Requires `NOTION_TOKEN` in `.env.local`
- **Database IDs**: Tasks=`29f795383d90808f874ef7a8e7857c01`, Projects=`29f795383d9080388644f9c25bdf2689`

## Workflow

1. **Query** → Use `utils.notion_helper` functions (query_database, get_items_by_status, find_item_by_name)
2. **Update** → Use direct API via helper functions (update_item_status, update_page_property)
3. **Store Prompts** → Save in Notes/Cursor Prompt fields
4. **Retrieve Context** → Pull from database for planning using get_page_content or query_database

## Test Results

✅ Module loads successfully
✅ CLI script works
✅ Can query databases
✅ Can update items

## Next Steps

- Use the prompts in `.cursor/notion-prompts.md` for common workflows
- Store prompts in database Notes fields for reuse
- Query databases for context when planning work
- Update statuses as items are completed

See `.cursor/notion-workflows.md` for detailed examples and workflows.

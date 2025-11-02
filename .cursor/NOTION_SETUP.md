# Notion Integration Setup - Complete ✅

## What Was Created

1. **`utils/notion_helper.py`** - Python module for programmatic Notion updates
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
from utils.notion_helper import update_item_status, get_items_by_status

# Update status
update_item_status("tasks", "Task name", "Done")

# Query database
tasks = get_items_by_status("tasks", "In progress")
```

### Using MCP Server (for queries)
Use MCP tools for reading/searching:
- `mcp_notion_API-post-database-query` - Query databases
- `mcp_notion_API-post-search` - Search for databases/pages
- `mcp_notion_API-retrieve-a-page` - Get page details

## Configuration

- **MCP Config**: Kept in `~/.cursor/mcp.json` (works for queries)
- **API Updates**: Use `utils/notion_helper.py` or `scripts/notion_update.py`
- **Environment**: Requires `NOTION_TOKEN` in `.env.local`

## Workflow

1. **Query** → Use MCP server (fast, reliable)
2. **Update** → Use direct API via helper functions
3. **Store Prompts** → Save in Notes/Cursor Prompt fields
4. **Retrieve Context** → Pull from database for planning

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


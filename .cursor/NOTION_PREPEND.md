# Notion Database Access Instructions

When working with Notion databases in this project:

**For queries/reading**: Use the Notion MCP server (`mcp_notion_API-post-database-query`, `mcp_notion_API-retrieve-a-page`, etc.)

**For updates**: Use `utils.notion_helper` functions:
- `update_item_status(db_type, item_name, status)` - Update status
- `update_page_property(page_id, property_name, value)` - Update any property
- `find_item_by_name(db_id, name)` - Find items
- `get_items_by_status(db_type, status)` - Query by status

**Database IDs**: Tasks=`29f795383d90808f874ef7a8e7857c01`, Projects=`29f795383d9080388644f9c25bdf2689`

**Status values**: "Not started", "In progress", "Done"

For text updates, use `{"rich_text": [{"text": {"content": "your text"}}]}` format.


# Notion Database Access Instructions

When working with Notion databases in this project:

**For queries/reading**: Use `utils.notion_helper` functions:
- `query_database(database_id, filter_dict)` - Query databases with filters
- `get_items_by_status(database_type, status_name)` - Get items by status
- `find_item_by_name(database_id, item_name)` - Find items by name
- `get_page_content(page_id)` - Retrieve page properties and content
- `get_database_id(database_type)` - Get database ID

**For updates**: Use `utils.notion_helper` functions:
- `update_item_status(db_type, item_name, status)` - Update status
- `update_page_property(page_id, property_name, value)` - Update any property
- `find_item_by_name(db_id, name)` - Find items
- `get_items_by_status(db_type, status)` - Query by status
- `create_task(title, project_id, notes)` - Create new tasks

**Database IDs**: Tasks=`29f795383d90808f874ef7a8e7857c01`, Projects=`29f795383d9080388644f9c25bdf2689`

**Status values**: "Not started", "In progress", "Done"

For text updates, use `{"rich_text": [{"text": {"content": "your text"}}]}` format.

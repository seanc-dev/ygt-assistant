Please use the following instructions to update the tasks and projects databases where relevant.

## Database IDs

- Tasks: `29f795383d90808f874ef7a8e7857c01`
- Projects: `29f795383d9080388644f9c25bdf2689`

## Status Values

- "Not started"
- "In progress"
- "Done"

## Approaches by Use Case

### For Queries (Read Operations)

**Use `utils.notion_helper` functions:**

- `query_database(database_id, filter_dict)` - Query databases with filters
- `get_items_by_status(database_type, status_name)` - Get items by status
- `find_item_by_name(database_id, item_name)` - Find item by name
- `get_page_content(page_id)` - Get page properties and content
- `get_database_id(database_type)` - Get database ID for tasks/projects

**Examples:**

```python
from utils.notion_helper import query_database, get_items_by_status, find_item_by_name, get_database_id

# Query with custom filter
db_id = get_database_id("tasks")
items = query_database(db_id, {"property": "Status", "status": {"equals": "In progress"}})

# Get items by status
tasks = get_items_by_status("tasks", "In progress")

# Find specific item
task = find_item_by_name(get_database_id("tasks"), "Task name")
```

### For Updates (Modify Existing Items)

**Use `utils.notion_helper` functions:**

- `update_item_status(database_type, item_name, new_status)` - Update task/project status
- `update_page_property(page_id, property_name, property_value)` - Update any property
- `find_item_by_name(database_id, item_name)` - Find item before updating

**Examples:**

```python
from utils.notion_helper import update_item_status, update_page_property

# Update status
update_item_status("tasks", "Task name", "Done")

# Update custom property
update_page_property(page_id, "Priority", {"select": {"name": "High"}})
```

**For text updates**, use format: `{"rich_text": [{"text": {"content": "your text"}}]}`

### For Creating Tasks (New Items)

**Use `utils.notion_helper.create_task()` function:**

```python
from utils.notion_helper import create_task

# Create a task linked to a project
create_task("Task title", "project-page-id", "Optional notes")
```

**Or use the convenience script:**

```python
from scripts.create_notion_tasks import create_task

create_task("Task title", "project-page-id", "Optional notes")
```

**Or modify `scripts/create_notion_tasks.py` main() function** and run:

```bash
python scripts/create_notion_tasks.py
```

### For Listing Items

**Use `utils.notion_helper` functions:**

- `get_items_by_status(database_type, status_name)` - Get all items with a status
- `query_database(database_id, filter_dict)` - Custom queries

**Or use CLI script:**

```bash
python scripts/notion_update.py tasks --list "In progress"
python scripts/notion_update.py projects --list "Done"
```

## CLI Scripts Available

1. **`scripts/notion_update.py`** - Update existing items or list items

   - `python scripts/notion_update.py tasks "Task name" "Done"`
   - `python scripts/notion_update.py tasks --list "In progress"`

2. **`scripts/create_notion_tasks.py`** - Create new tasks (modify main() function)

## Adding Todos Workflow

1. Query for project using `find_item_by_name()` or `query_database()` to get project ID
2. Create tasks using `utils.notion_helper.create_task()` or modify `scripts/create_notion_tasks.py`
3. Link tasks to projects via the `project_id` parameter
4. Add relevant properties (Status, Project relation, Notes, etc.)

If you need to create a new script to achieve the requested functinoality, prioritise updating existing scripts. If new functionality is created/added, update .cursor/commands/notiontodo.md with references to it.

# Notion Database Prompts for Cursor

Quick reference prompts you can use in Cursor to work with Notion databases.

## Status Updates

### Mark Tasks as Done

```
Update the task "[task name]" to "Done" status using utils.notion_helper.update_item_status()
```

### Move Items to In Progress

```
Move the task "[task name]" to "In progress" status
Move the project "[project name]" to "In progress" status
```

### Update Multiple Items

```
Mark all completed tasks as "Done" - review tasks with status "In progress" and update those that are finished
```

## Database Queries

### Review Current Work

```
Query the Tasks database for items with status "In progress" using utils.notion_helper.get_items_by_status() and show me what I'm currently working on
Show me all projects that are "In progress" using utils.notion_helper.get_items_by_status()
```

### Find Next Items

```
Find tasks that are "Not started" and have high priority using utils.notion_helper.query_database()
What are the next 3 items I should focus on from the Tasks database?
Show me all "Not started" projects using utils.notion_helper.get_items_by_status()
```

### Search by Content

```
Search the Tasks database for items containing "[keyword]" in the name using utils.notion_helper.find_item_by_name() or query_database()
Find all tasks related to "[topic]" in the Projects database using utils.notion_helper.query_database()
```

## Context Retrieval

### Pull Project Context

```
Pull context from Notion Tasks database for tasks related to "[project name]" using utils.notion_helper.query_database()
Get all information from the Projects database about "[project name]" using utils.notion_helper.find_item_by_name() and get_page_content()
Retrieve the Notes field from task "[task name]" using utils.notion_helper.find_item_by_name() and get_page_content() and use it as context
```

### Review Database State

```
Review the Tasks database using utils.notion_helper.get_items_by_status() and summarize what's in progress, what's done, and what needs to be started
Show me a summary of all projects and their current status using utils.notion_helper.query_database()
What's the status of all high-priority tasks using utils.notion_helper.query_database()?
```

## Update Item

### Add Text Updates

```
Add the following text to the Notes field of task "[task name]": [update text] using utils.notion_helper.update_page_property()
Update the Notes field for project "[project name]" with: [update text] using utils.notion_helper.update_page_property()
Append "[text]" to the Notes field of task "[task name]" using utils.notion_helper.get_page_content() and update_page_property()
Add a note to task "[task name]": [note text] using utils.notion_helper.update_page_property()
```

## Planning & Review

### Daily Planning

```
Review Notion Tasks database using utils.notion_helper.get_items_by_status() and identify what I should work on today
Show me tasks that are high priority and not started using utils.notion_helper.query_database()
What projects need attention this week using utils.notion_helper.get_items_by_status()?
```

### Status Reviews

```
Review all in-progress tasks using utils.notion_helper.get_items_by_status() and update any that are actually completed
Check Projects database for items that should be marked as Done using utils.notion_helper.get_items_by_status()
Update task statuses based on completion: mark finished items as Done using utils.notion_helper.update_item_status()
```

### Workflow Integration

```
1. Query Tasks database for in-progress items using utils.notion_helper.get_items_by_status()
2. For each item, check if it's completed
3. Update completed items to "Done" status using utils.notion_helper.update_item_status()
4. Show me remaining in-progress items
```

## Combined Workflows

### Complete Task Flow

```
1. Find task "[task name]" in Tasks database using utils.notion_helper.find_item_by_name()
2. Retrieve its Notes field for context using utils.notion_helper.get_page_content()
3. After completion, update the task status to "Done" using utils.notion_helper.update_item_status()
4. Add a completion note to the task's Notes field using utils.notion_helper.update_page_property()
```

### Project Status Update

```
1. Query Projects database for all items using utils.notion_helper.query_database()
2. Review each project's status
3. Update projects that are completed to "Done" using utils.notion_helper.update_item_status()
4. Move projects that are starting to "In progress" using utils.notion_helper.update_item_status()
5. Show summary of changes
```

## Tips

- Use exact status names: "Not started", "In progress", "Done"
- Item names are case-sensitive and match exactly
- Use `utils.notion_helper` functions for all operations (queries and updates)
- Use `update_page_property()` with `{"rich_text": [{"text": {"content": "your text"}}]}` to update text fields
- All functions use the Notion API directly - no MCP server required

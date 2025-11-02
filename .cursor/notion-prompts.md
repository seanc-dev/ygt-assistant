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
Query the Tasks database for items with status "In progress" and show me what I'm currently working on
Show me all projects that are "In progress"
```

### Find Next Items

```
Find tasks that are "Not started" and have high priority
What are the next 3 items I should focus on from the Tasks database?
Show me all "Not started" projects
```

### Search by Content

```
Search the Tasks database for items containing "[keyword]" in the name or notes
Find all tasks related to "[topic]" in the Projects database
```

## Context Retrieval

### Pull Project Context

```
Pull context from Notion Tasks database for tasks related to "[project name]"
Get all information from the Projects database about "[project name]"
Retrieve the Notes field from task "[task name]" and use it as context
```

### Review Database State

```
Review the Tasks database and summarize what's in progress, what's done, and what needs to be started
Show me a summary of all projects and their current status
What's the status of all high-priority tasks?
```

## Update Item

### Add Text Updates

```
Add the following text to the Notes field of task "[task name]": [update text]
Update the Notes field for project "[project name]" with: [update text]
Append "[text]" to the Notes field of task "[task name]"
Add a note to task "[task name]": [note text]
```

## Planning & Review

### Daily Planning

```
Review Notion Tasks database and identify what I should work on today
Show me tasks that are high priority and not started
What projects need attention this week?
```

### Status Reviews

```
Review all in-progress tasks and update any that are actually completed
Check Projects database for items that should be marked as Done
Update task statuses based on completion: mark finished items as Done
```

### Workflow Integration

```
1. Query Tasks database for in-progress items
2. For each item, check if it's completed
3. Update completed items to "Done" status
4. Show me remaining in-progress items
```

## Combined Workflows

### Complete Task Flow

```
1. Find task "[task name]" in Tasks database
2. Retrieve its Notes field for context
3. After completion, update the task status to "Done"
4. Add a completion note to the task's Notes field
```

### Project Status Update

```
1. Query Projects database for all items
2. Review each project's status
3. Update projects that are completed to "Done"
4. Move projects that are starting to "In progress"
5. Show summary of changes
```

## Tips

- Use exact status names: "Not started", "In progress", "Done"
- Item names are case-sensitive and match exactly
- Use MCP server for queries (fast and reliable)
- Use `utils.notion_helper` functions for updates
- Use `update_page_property()` with `{"rich_text": [{"text": {"content": "your text"}}]}` to update text fields

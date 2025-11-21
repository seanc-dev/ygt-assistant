# Workroom assistant contract: context_input

This note documents the `context_input` payload Workroom sends to the LLM when proposing operations. It describes how the payload is shaped, how it is truncated, and how the assistant should react to the provided data.

## Shape (WorkroomContextSpace)

`context_input` is emitted from a `WorkroomContextSpace` built from the caller's current Workroom context. The payload is JSON and intentionally compact:

- `anchor`: `{ "task_id": string | null, "project_id": string | null }` — the current Workroom focus task/project.
- `projects`: `[{ "id", "name", "status" }]` — available projects (truncated, see below).
- `tasks`: `[{ "id", "title", "status", "project_id" }]` — available tasks (truncated).
- `actions`: `[{ "id", "preview", "source_type" }]` — queued action items (truncated).
- `truncated`: `{ "projects": number, "tasks": number, "actions": number }` — counts of omitted items per list. Only present when any count is non-zero.

Any list may be absent when no items are available. The payload is omitted entirely when there is no anchor and every list is empty.

## Truncation rules

The Workroom context fed to the assistant is trimmed to keep prompts small and predictable:

- Projects: first 8 entries
- Tasks: first 12 entries
- Actions: first 8 entries

If more records exist, the omitted counts appear under `truncated`. The assistant should never invent names beyond the visible items; if the user references something outside the lists, it should ask them to surface or open it.

## Assistant guardrails

- Prefer the `anchor` task/project whenever the user says "this task" or "current project".
- Operate only on projects, tasks, and actions listed in `context_input`. If the desired item is missing (or the list is truncated), ask the user to pick from the visible options before proposing operations.
- Continue honoring the existing Workroom rules around current project enforcement and semantic references—`context_input` is an additional narrowing filter, not a replacement.

## Example exchange

**context_input**

```json
{
  "anchor": {"task_id": "task-123", "project_id": "proj-9"},
  "projects": [
    {"id": "proj-9", "name": "Inbox Zero", "status": "active"},
    {"id": "proj-10", "name": "Q4 Launch", "status": "active"}
  ],
  "tasks": [
    {"id": "task-123", "title": "Triage inbox", "status": "backlog", "project_id": "proj-9"},
    {"id": "task-124", "title": "Draft launch email", "status": "ready", "project_id": "proj-10"}
  ],
  "actions": [
    {"id": "act-1", "preview": "Reply about licensing", "source_type": "email"}
  ],
  "truncated": {"projects": 1, "tasks": 4, "actions": 0}
}
```

**User:** "Mark the current task as done and link the licensing email."

**Assistant (valid):** propose `update_task_status` with `task: "this task"`, plus `link_action_to_task` with the visible action preview. If the user asks about a task or project not shown, it should respond with a `chat` operation asking them to open it in the Workroom before proceeding.

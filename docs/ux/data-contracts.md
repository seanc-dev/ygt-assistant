# Data Contracts

## TypeScript Interfaces

### Project
```typescript
interface Project {
  id: string;
  name: string;
  description?: string;
  priority: "low" | "medium" | "high";
  context: {
    notes?: string;
    pinned_refs: string[];
  };
  children: Task[];
}
```

### Task
```typescript
interface Task {
  id: string;
  project_id: string;
  title: string;
  status: "todo" | "doing" | "done" | "blocked";
  due?: string; // ISO datetime
  importance: "low" | "medium" | "high";
  context: {
    notes?: string;
    pinned_refs: string[];
  };
  children: Thread[];
}
```

### Thread
```typescript
interface Thread {
  id: string;
  task_id: string;
  title: string;
  messages: Message[];
  context_refs: string[];
  prefs: {
    translation?: boolean;
    trust?: "training-wheels" | "standard" | "autonomous";
  };
}
```

### ActionItem
```typescript
interface ActionItem {
  action_id: string; // UUID
  source: "email" | "teams" | "doc";
  category: "needs_response" | "needs_approval" | "fyi";
  priority: "low" | "medium" | "high";
  preview: string;
  thread_id?: string;
  defer_until?: string; // ISO datetime
  defer_bucket?: "afternoon" | "tomorrow" | "this_week" | "next_week";
  added_to_today?: boolean;
}
```

### ScheduleBlock
```typescript
interface ScheduleBlock {
  id: string;
  kind: "focus" | "admin" | "meeting";
  tasks: string[]; // task IDs
  start: string; // ISO datetime
  end: string; // ISO datetime
  alt_plan_id?: string;
}
```

## Pydantic Models

### Project (Python)
```python
from pydantic import BaseModel
from typing import List, Optional

class ProjectContext(BaseModel):
    notes: Optional[str] = None
    pinned_refs: List[str] = []

class Project(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    priority: str  # "low" | "medium" | "high"
    context: ProjectContext
    children: List["Task"] = []
```

### Task (Python)
```python
class TaskContext(BaseModel):
    notes: Optional[str] = None
    pinned_refs: List[str] = []

class Task(BaseModel):
    id: str
    project_id: str
    title: str
    status: str  # "todo" | "doing" | "done" | "blocked"
    due: Optional[str] = None  # ISO datetime
    importance: str  # "low" | "medium" | "high"
    context: TaskContext
    children: List["Thread"] = []
```

### Thread (Python)
```python
class ThreadPrefs(BaseModel):
    translation: Optional[bool] = None
    trust: Optional[str] = None  # "training-wheels" | "standard" | "autonomous"

class Thread(BaseModel):
    id: str
    task_id: str
    title: str
    messages: List[dict] = []
    context_refs: List[str] = []
    prefs: ThreadPrefs
```

### ActionItem (Python)
```python
class ActionItem(BaseModel):
    action_id: str  # UUID
    source: str  # "email" | "teams" | "doc"
    category: str  # "needs_response" | "needs_approval" | "fyi"
    priority: str  # "low" | "medium" | "high"
    preview: str
    thread_id: Optional[str] = None
    defer_until: Optional[str] = None  # ISO datetime
    defer_bucket: Optional[str] = None  # "afternoon" | "tomorrow" | "this_week" | "next_week"
    added_to_today: Optional[bool] = None
```

### ScheduleBlock (Python)
```python
class ScheduleBlock(BaseModel):
    id: str
    kind: str  # "focus" | "admin" | "meeting"
    tasks: List[str] = []  # task IDs
    start: str  # ISO datetime
    end: str  # ISO datetime
    alt_plan_id: Optional[str] = None
```

## API Endpoints

### GET /api/queue
Response:
```json
{
  "items": [ActionItem],
  "total": number
}
```

### POST /api/queue/{action_id}/defer
Request:
```json
{
  "bucket": "afternoon" | "tomorrow" | "this_week" | "next_week"
}
```

### POST /api/queue/{action_id}/add-to-today
Request:
```json
{
  "kind": "admin" | "work",
  "tasks": ["task_id1", "task_id2"]
}
```

### GET /api/schedule/today
Response:
```json
{
  "events": [CalendarEvent],
  "blocks": [ScheduleBlock]
}
```

### POST /api/schedule/alternatives
Response:
```json
{
  "plans": [
    {
      "id": "plan_a",
      "type": "focus-first",
      "blocks": [ScheduleBlock]
    },
    {
      "id": "plan_b",
      "type": "meeting-friendly",
      "blocks": [ScheduleBlock]
    },
    {
      "id": "plan_c",
      "type": "balanced",
      "blocks": [ScheduleBlock]
    }
  ],
  "overload": {
    "detected": boolean,
    "suggestions": [
      {
        "action": "reschedule" | "decline",
        "item_id": string,
        "requires_approval": boolean
      }
    ]
  }
}
```

### GET /api/workroom/tree
Response:
```json
{
  "projects": [Project]
}
```

### GET /api/settings
Response:
```json
{
  "work_hours": {
    "start": "09:00",
    "end": "17:00",
    "timezone": "UTC"
  },
  "translation": {
    "enabled": boolean,
    "rules": {
      "outbound": boolean,
      "inbound": boolean,
      "internal": boolean,
      "external": boolean
    }
  },
  "trust_level": "training-wheels" | "standard" | "autonomous",
  "ui_prefs": {
    "thread_open_behavior": "new_tab" | "replace",
    "brief": {
      "weather": boolean,
      "news": boolean,
      "tone": string
    }
  }
}
```


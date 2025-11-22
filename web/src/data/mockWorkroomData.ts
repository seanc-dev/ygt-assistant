import type { FocusAnchor } from "../lib/focusContext";
import type { Task, TaskStatus } from "../hooks/useWorkroomStore";
import type { WorkroomContext, WorkroomNeighborhood } from "../lib/workroomContext";

export type WorkroomContextSpace = {
  summary: string | null;
  highlights: string[];
  questions: string[];
};

const defaultContextSpace: WorkroomContextSpace = {
  summary: null,
  highlights: [],
  questions: [],
};

const initialContextSpaceByAnchor: Record<string, WorkroomContextSpace> = {
  "task:task-1": {
    summary: "Drafting new workroom UX with design alignment and acceptance criteria",
    highlights: ["Sync with design", "Capture PRD updates"],
    questions: ["Do we have sign-off on the UX flow?"],
  },
  "event:event-1": {
    summary: "Design review for workroom improvements",
    highlights: ["Share updated mockups"],
    questions: ["Any blockers from engineering?"],
  },
};

export const mockContextSpaceByAnchor: Record<string, WorkroomContextSpace> = {
  ...initialContextSpaceByAnchor,
};

const sanitizeContextSpace = (input?: Partial<WorkroomContextSpace> | null) => {
  const output: Partial<WorkroomContextSpace> = {};
  if (input?.summary === null || typeof input?.summary === "string") {
    output.summary = input.summary;
  }
  if (Array.isArray(input?.highlights)) {
    output.highlights = input.highlights.filter((item): item is string => typeof item === "string");
  }
  if (Array.isArray(input?.questions)) {
    output.questions = input.questions.filter((item): item is string => typeof item === "string");
  }
  return output;
};

const anchorKey = (anchor: FocusAnchor) => `${anchor.type}:${anchor.id || ""}`;

export const resetMockContextSpaceStore = () => {
  Object.keys(mockContextSpaceByAnchor).forEach((key) => delete mockContextSpaceByAnchor[key]);
  Object.entries(initialContextSpaceByAnchor).forEach(([key, value]) => {
    mockContextSpaceByAnchor[key] = { ...value };
  });
};

export const getMockContextSpace = (anchor: FocusAnchor): WorkroomContextSpace & { anchor: FocusAnchor } => {
  const stored = mockContextSpaceByAnchor[anchorKey(anchor)];
  const sanitized = sanitizeContextSpace(stored);
  return {
    anchor,
    summary: sanitized.summary ?? defaultContextSpace.summary,
    highlights: sanitized.highlights ?? defaultContextSpace.highlights,
    questions: sanitized.questions ?? defaultContextSpace.questions,
  };
};

export const saveMockContextSpace = (
  anchor: FocusAnchor,
  input?: Partial<WorkroomContextSpace> | null
): (WorkroomContextSpace & { anchor: FocusAnchor }) => {
  const sanitized = sanitizeContextSpace(input);
  const existing = mockContextSpaceByAnchor[anchorKey(anchor)] ?? defaultContextSpace;
  const nextValue: WorkroomContextSpace = {
    summary: sanitized.summary ?? existing.summary ?? defaultContextSpace.summary,
    highlights: sanitized.highlights ?? existing.highlights ?? defaultContextSpace.highlights,
    questions: sanitized.questions ?? existing.questions ?? defaultContextSpace.questions,
  };
  mockContextSpaceByAnchor[anchorKey(anchor)] = nextValue;
  return { anchor, ...nextValue };
};

export type MockEvent = {
  id: string;
  title: string;
  start: string;
  end: string;
};

const mockTasks: (Task & { linkedEventId?: string | null })[] = [
  {
    id: "task-1",
    projectId: "alpha",
    title: "Draft new workroom UX",
    status: "doing",
    priority: "high",
    priority_pin: true,
    due: new Date().toISOString(),
    tags: ["workroom", "ux"],
    microNote: "Align with design before noon",
    chats: [],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    linkedEventId: "event-1",
  },
  {
    id: "task-2",
    projectId: "alpha",
    title: "Review Q2 roadmap",
    status: "backlog",
    priority: "medium",
    priority_pin: true,
    due: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
    tags: ["roadmap"],
    microNote: "Draft brief before leadership sync",
    chats: [],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },
  {
    id: "task-3",
    projectId: "beta",
    title: "Sync with design",
    status: "ready",
    priority: "high",
    chats: [],
    microNote: "Prep talking points",
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    linkedEventId: "event-2",
  },
  {
    id: "task-4",
    projectId: "beta",
    title: "Write meeting summary",
    status: "blocked",
    priority: "low",
    chats: [],
    microNote: "Waiting on approvals",
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },
  {
    id: "task-5",
    projectId: "alpha",
    title: "File status report",
    status: "done",
    priority: "medium",
    chats: [],
    microNote: "Shipped last week",
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },
];

const mockEvents: MockEvent[] = [
  {
    id: "event-1",
    title: "Design review",
    start: new Date().toISOString(),
    end: new Date(Date.now() + 30 * 60 * 1000).toISOString(),
  },
  {
    id: "event-2",
    title: "Sprint planning",
    start: new Date(Date.now() + 60 * 60 * 1000).toISOString(),
    end: new Date(Date.now() + 90 * 60 * 1000).toISOString(),
  },
];

const mockProjects = [
  { id: "alpha", name: "Project Alpha" },
  { id: "beta", name: "Project Beta" },
];

const mockDocs = [
  { id: "doc-1", title: "Product requirements" },
  { id: "doc-2", title: "Sprint notes" },
  { id: "doc-3", title: "User research" },
];

const mockQueueItems = [
  { id: "queue-1", subject: "New request", source: "queue" },
  { id: "queue-2", subject: "Bug triage", source: "queue" },
];

const mockMentions = [
  { id: "mention-1", subject: "Design doc mention", source: "mentions" },
];

const mockDocUpdates = [
  { id: "doc-update-1", subject: "PRD updated", source: "docs" },
];

const mockEmails = [
  { id: "email-1", subject: "Status request", source: "email" },
];

// Mock Chats
export const mockChats = [
  {
    id: "chat-1",
    taskId: "task-1",
    title: "UX Discussion",
    createdAt: new Date(Date.now() - 86400000).toISOString(),
    updatedAt: new Date().toISOString(),
    messageCount: 3,
  },
];

export const mockMessages = [
  {
    id: "msg-1",
    threadId: "chat-1",
    role: "user",
    content: "Can we review the new workroom layout?",
    ts: new Date(Date.now() - 3600000).toISOString(),
  },
  {
    id: "msg-2",
    threadId: "chat-1",
    role: "assistant",
    content: "I've analyzed the current layout. The main focus area seems a bit cluttered. Shall we simplify the sidebar?",
    ts: new Date(Date.now() - 3500000).toISOString(),
  },
  {
    id: "msg-3",
    threadId: "chat-1",
    role: "user",
    content: "Yes, let's try moving the context panel to the right.",
    ts: new Date(Date.now() - 3400000).toISOString(),
  },
];

export const getMockTasks = () => {
  // Attach mock chats to tasks
  return mockTasks.map(task => ({
    ...task,
    chats: mockChats.filter(c => c.taskId === task.id)
  }));
};

export const updateMockTask = (taskId: string, updates: Partial<Task>) => {
  const idx = mockTasks.findIndex((task) => task.id === taskId);
  if (idx >= 0) {
    mockTasks[idx] = { ...mockTasks[idx], ...updates };
  }
};

export const updateMockTaskStatus = (taskId: string, status: TaskStatus) => {
  const idx = mockTasks.findIndex((task) => task.id === taskId);
  if (idx >= 0) {
    mockTasks[idx] = { ...mockTasks[idx], status };
  }
};

export const getMockEvents = () => mockEvents;
export const getMockQueueItems = () => mockQueueItems;
export const getMockMentions = () => mockMentions;
export const getMockDocUpdates = () => mockDocUpdates;
export const getMockEmails = () => mockEmails;

export const statusLabelMap: Record<TaskStatus, string> = {
  backlog: "Backlog",
  ready: "Ready",
  doing: "Doing",
  blocked: "Blocked",
  done: "Done",
};

export const formatTimeWindow = (start?: string, end?: string) => {
  if (!start && !end) return "No scheduled time";
  const startDate = start ? new Date(start) : undefined;
  const endDate = end ? new Date(end) : undefined;
  if (!startDate) return "No scheduled time";
  const dayLabel = startDate.toLocaleDateString(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
  });
  const startLabel = startDate.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
  const endLabel = endDate ? endDate.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" }) : "";
  return `${dayLabel} · ${startLabel}${endLabel ? `–${endLabel}` : ""}`;
};

const buildNeighborhoodForTask = (taskId: string): WorkroomNeighborhood => {
  const tasks = mockTasks
    .filter((task) => task.id !== taskId)
    .slice(0, 3)
    .map(({ id, title, status }) => ({ id, title, status }));
  const task = mockTasks.find((t) => t.id === taskId);
  const events = task?.linkedEventId
    ? mockEvents.filter((event) => event.id === task.linkedEventId).map(({ id, title, start, end }) => ({ id, title, start, end }))
    : mockEvents.slice(0, 1).map(({ id, title, start, end }) => ({ id, title, start, end }));
  const docs = mockDocs.slice(0, 2);
  return { tasks, events, docs, queueItems: [] };
};

const buildNeighborhoodForEvent = (eventId: string): WorkroomNeighborhood => {
  const tasks = mockTasks
    .filter((task) => task.linkedEventId === eventId)
    .slice(0, 3)
    .map(({ id, title, status }) => ({ id, title, status }));
  const events = mockEvents
    .filter((event) => event.id !== eventId)
    .slice(0, 2)
    .map(({ id, title, start, end }) => ({ id, title, start, end }));
  const docs = mockDocs.slice(0, 1);
  return { tasks, events, docs, queueItems: [] };
};

const buildNeighborhoodForProject = (projectId?: string): WorkroomNeighborhood => {
  const tasks = mockTasks
    .filter((task) => (projectId ? task.projectId === projectId : true))
    .slice(0, 5)
    .map(({ id, title, status }) => ({ id, title, status }));
  const events = mockEvents.slice(0, 2).map(({ id, title, start, end }) => ({ id, title, start, end }));
  const docs = mockDocs.slice(0, 2);
  return { tasks, events, docs, queueItems: [] };
};

const buildNeighborhoodForPortfolio = (): WorkroomNeighborhood => ({
  tasks: mockTasks.slice(0, 5).map(({ id, title, status }) => ({ id, title, status })),
  events: mockEvents.slice(0, 2).map(({ id, title, start, end }) => ({ id, title, start, end })),
  docs: mockDocs,
  queueItems: [{ id: "queue-1", subject: "New request" }],
});

export const buildWorkroomContext = (anchor: FocusAnchor): WorkroomContext | null => {
  switch (anchor.type) {
    case "task": {
      if (!anchor.id) return null;
      const task = mockTasks.find((t) => t.id === anchor.id);
      const anchorInfo: WorkroomContext["anchor"] = {
        type: "task",
        id: anchor.id,
        title: task?.title || anchor.id,
        status: task?.status,
        priority: task?.priority,
        linkedEventId: task?.linkedEventId ?? null,
      };
      return { anchor: anchorInfo, neighborhood: buildNeighborhoodForTask(anchor.id) };
    }
    case "event": {
      if (!anchor.id) return null;
      const event = mockEvents.find((e) => e.id === anchor.id);
      const linkedTasks = mockTasks.filter((t) => t.linkedEventId === anchor.id).map((t) => t.id);
      const anchorInfo: WorkroomContext["anchor"] = {
        type: "event",
        id: anchor.id,
        title: event?.title || anchor.id,
        start: event?.start,
        end: event?.end,
        linkedTaskIds: linkedTasks,
      };
      return { anchor: anchorInfo, neighborhood: buildNeighborhoodForEvent(anchor.id) };
    }
    case "project": {
      const project = anchor.id ? mockProjects.find((p) => p.id === anchor.id) : undefined;
      const anchorInfo: WorkroomContext["anchor"] = {
        type: "project",
        id: anchor.id || "unknown",
        name: project?.name || anchor.id || "Project",
      };
      return { anchor: anchorInfo, neighborhood: buildNeighborhoodForProject(anchor.id) };
    }
    case "portfolio": {
      const anchorInfo: WorkroomContext["anchor"] = {
        type: "portfolio",
        id: "my_work",
        label: "My work",
      };
      return { anchor: anchorInfo, neighborhood: buildNeighborhoodForPortfolio() };
    }
    case "today": {
      const anchorInfo: WorkroomContext["anchor"] = {
        type: "portfolio",
        id: anchor.id || "today",
        label: "Today",
      };
      return { anchor: anchorInfo, neighborhood: buildNeighborhoodForPortfolio() };
    }
    case "triage": {
      const anchorInfo: WorkroomContext["anchor"] = {
        type: "portfolio",
        id: anchor.id || "triage",
        label: "Triage",
      };
      return { anchor: anchorInfo, neighborhood: buildNeighborhoodForPortfolio() };
    }
    default:
      return null;
  }
};

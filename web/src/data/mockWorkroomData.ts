import type { FocusAnchor } from "../lib/focusContext";
import type { Task, TaskStatus } from "../hooks/useWorkroomStore";
import type { WorkroomContext, WorkroomNeighborhood } from "../lib/workroomContext";

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
    due: new Date().toISOString(),
    tags: ["workroom", "ux"],
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
    due: new Date().toISOString(),
    tags: ["roadmap"],
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

export const getMockTasks = () => mockTasks;

export const updateMockTaskStatus = (taskId: string, status: TaskStatus) => {
  const idx = mockTasks.findIndex((task) => task.id === taskId);
  if (idx >= 0) {
    mockTasks[idx] = { ...mockTasks[idx], status };
  }
};

export const getMockEvents = () => mockEvents;

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
  return { tasks, events, docs: [], queueItems: [] };
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
  return { tasks, events, docs: [], queueItems: [] };
};

const buildNeighborhoodForProject = (projectId?: string): WorkroomNeighborhood => {
  const tasks = mockTasks
    .filter((task) => (projectId ? task.projectId === projectId : true))
    .slice(0, 5)
    .map(({ id, title, status }) => ({ id, title, status }));
  const events = mockEvents.slice(0, 2).map(({ id, title, start, end }) => ({ id, title, start, end }));
  return { tasks, events, docs: [], queueItems: [] };
};

const buildNeighborhoodForPortfolio = (): WorkroomNeighborhood => ({
  tasks: mockTasks.slice(0, 5).map(({ id, title, status }) => ({ id, title, status })),
  events: mockEvents.slice(0, 2).map(({ id, title, start, end }) => ({ id, title, start, end })),
  docs: [{ id: "doc-1", title: "Product requirements" }],
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
    default:
      return null;
  }
};

import {
  getMockDocUpdates,
  getMockEmails,
  getMockEvents,
  getMockMentions,
  getMockQueueItems,
  getMockTasks,
  updateMockTask,
} from "../data/mockWorkroomData";
import type { Task } from "../hooks/useWorkroomStore";

export type MyWorkGroupKey = "overdue" | "doing" | "ready" | "blocked";

export type MyWorkGroup = {
  key: MyWorkGroupKey;
  label: string;
  tasks: Task[];
};

export type InboxDigestItem = {
  id: string;
  subject: string;
  source: "email" | "docs" | "mentions" | "queue";
  timestamp?: string;
  relatedTaskId?: string;
};

export type InboxDigestGroup = {
  source: InboxDigestItem["source"];
  label: string;
  items: InboxDigestItem[];
};

const groupLabels: Record<MyWorkGroupKey, string> = {
  overdue: "Overdue",
  doing: "Doing",
  ready: "Ready",
  blocked: "Blocked",
};

export function getPinnedTasks(tasks: Task[] = getMockTasks()): Task[] {
  return tasks.filter((task) => task.priority_pin);
}

export function getMyWorkGrouped(tasks: Task[] = getMockTasks()): MyWorkGroup[] {
  const now = Date.now();
  const groups: Record<MyWorkGroupKey, Task[]> = {
    overdue: [],
    doing: [],
    ready: [],
    blocked: [],
  };

  tasks.forEach((task) => {
    const dueDate = task.due ? Date.parse(task.due) : undefined;
    const isOverdue = dueDate ? dueDate < now && task.status !== "done" : false;
    if (isOverdue) {
      groups.overdue.push(task);
      return;
    }

    if (task.status === "doing") {
      groups.doing.push(task);
      return;
    }
    if (task.status === "ready") {
      groups.ready.push(task);
      return;
    }
    if (task.status === "blocked") {
      groups.blocked.push(task);
    }
  });

  return (Object.keys(groups) as MyWorkGroupKey[]).map((key) => ({
    key,
    label: groupLabels[key],
    tasks: groups[key],
  }));
}

export function getInboxDigest(): InboxDigestGroup[] {
  const emails = getMockEmails();
  const docs = getMockDocUpdates();
  const mentions = getMockMentions();
  const queue = getMockQueueItems();

  const buildGroup = (
    source: InboxDigestItem["source"],
    label: string,
    items: Array<{ id: string; subject: string; relatedTaskId?: string }>
  ): InboxDigestGroup | null => {
    if (!items.length) return null;
    return {
      source,
      label,
      items: items.map((item, index) => ({
        id: item.id,
        subject: item.subject,
        source,
        relatedTaskId: item.relatedTaskId,
        timestamp: new Date(Date.now() - index * 600000).toISOString(),
      })),
    };
  };

  const groups: Array<InboxDigestGroup | null> = [
    buildGroup("email", "Email", emails),
    buildGroup("docs", "Docs", docs),
    buildGroup("mentions", "Mentions", mentions),
    buildGroup("queue", "Queue", queue),
  ];

  return groups.filter(Boolean) as InboxDigestGroup[];
}

export function toggleTaskPin(taskId: string, nextState: boolean) {
  updateMockTask(taskId, { priority_pin: nextState });
}

export function getTodayEvents() {
  return getMockEvents();
}

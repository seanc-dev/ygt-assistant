import { api } from "./api";
import type { Task, Project, ChatMeta, TaskDoc } from "../hooks/useWorkroomStore";
import type { ActionEmbed } from "./actionEmbeds";

const BASE = process.env.NEXT_PUBLIC_ADMIN_API_BASE || 
  (process.env.NODE_ENV === "development" ? "http://localhost:8000" : "https://api.coachflow.nz");

async function req(path: string, opts: RequestInit = {}) {
  const res = await fetch(`${BASE}${path}`, {
    ...opts,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(opts.headers || {}),
    },
  });
  if (!res.ok) {
    const error = new Error(`${res.status} ${res.statusText}`);
    (error as any).status = res.status;
    throw error;
  }
  return res.json();
}

export const workroomApi = {
  // Projects
  getProjects: (): Promise<{ ok: boolean; projects: Project[] }> =>
    req("/api/workroom/projects"),

  getProject: (projectId: string): Promise<{ ok: boolean; project: Project }> =>
    req(`/api/workroom/projects/${encodeURIComponent(projectId)}`),

  createProject: (data: { title: string; brief?: string }): Promise<{ ok: boolean; project: Project }> =>
    req("/api/workroom/projects", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // Tasks
  getTasks: (projectId: string): Promise<{ ok: boolean; tasks: Task[] }> =>
    req(`/api/workroom/projects/${encodeURIComponent(projectId)}/tasks`),

  getTask: (taskId: string): Promise<{ ok: boolean; task: Task }> =>
    req(`/api/workroom/tasks/${encodeURIComponent(taskId)}`),

  createTask: (data: {
    projectId: string;
    title: string;
    status?: string;
    priority?: string;
    due?: string;
    tags?: string[];
  }): Promise<{ ok: boolean; task: Task }> =>
    req("/api/workroom/tasks", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  updateTaskStatus: (taskId: string, status: string): Promise<{ ok: boolean }> =>
    req(`/api/workroom/tasks/${encodeURIComponent(taskId)}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    }),

  updateTask: (taskId: string, data: Partial<Task>): Promise<{ ok: boolean; task: Task }> =>
    req(`/api/workroom/tasks/${encodeURIComponent(taskId)}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  // Task Doc
  getTaskDoc: (taskId: string): Promise<{ ok: boolean; doc: TaskDoc | null }> =>
    req(`/api/workroom/tasks/${encodeURIComponent(taskId)}/doc`),

  updateTaskDoc: (taskId: string, contentJSON: any): Promise<{ ok: boolean; doc: TaskDoc }> =>
    req(`/api/workroom/tasks/${encodeURIComponent(taskId)}/doc`, {
      method: "PUT",
      body: JSON.stringify({ contentJSON }),
    }),

  // Chats
  getChats: (taskId: string): Promise<{ ok: boolean; chats: ChatMeta[] }> =>
    req(`/api/workroom/tasks/${encodeURIComponent(taskId)}/chats`),

  createChat: (taskId: string, data: { title: string }): Promise<{ ok: boolean; chat: ChatMeta }> =>
    req(`/api/workroom/tasks/${encodeURIComponent(taskId)}/chats`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // Messages (reuse existing API)
  getThread: api.getThread,
  sendMessage: api.sendMessage,

  // Action Embeds
  approveActionEmbed: (embedId: string, messageId: string): Promise<{ ok: boolean; embed: ActionEmbed }> =>
    req(`/api/workroom/embeds/${encodeURIComponent(embedId)}/approve`, {
      method: "POST",
      body: JSON.stringify({ messageId }),
    }),

  editActionEmbed: (embedId: string, messageId: string, edits: Partial<ActionEmbed>): Promise<{ ok: boolean; embed: ActionEmbed }> =>
    req(`/api/workroom/embeds/${encodeURIComponent(embedId)}/edit`, {
      method: "POST",
      body: JSON.stringify({ messageId, edits }),
    }),

  declineActionEmbed: (embedId: string, messageId: string): Promise<{ ok: boolean }> =>
    req(`/api/workroom/embeds/${encodeURIComponent(embedId)}/decline`, {
      method: "POST",
      body: JSON.stringify({ messageId }),
    }),
};


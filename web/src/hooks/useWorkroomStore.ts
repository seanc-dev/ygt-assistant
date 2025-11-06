import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

// For SSR compatibility
const isClient = typeof window !== "undefined";

export type TaskStatus = "backlog" | "ready" | "doing" | "blocked" | "done";

export interface Project {
  id: string;
  title: string;
  brief?: string;
  createdAt: string;
  updatedAt: string;
}

export interface ChatMeta {
  id: string;
  title: string;
  pinned?: boolean;
  lastMessageAt?: string;
}

export interface TaskDoc {
  id: string;
  contentJSON: any; // TipTap JSON
  updatedAt: string;
}

export interface Task {
  id: string;
  projectId: string;
  title: string;
  status: TaskStatus;
  priority?: string;
  due?: string;
  tags?: string[];
  doc?: TaskDoc;
  chats: ChatMeta[];
  unreadCount?: number;
  createdAt: string;
  updatedAt: string;
}

export interface WorkroomState {
  // View state
  view: "doc" | "chats" | "kanban";
  openChatIds: string[];
  activeChatId: string | null;
  contextWidth: number;
  lastFocusedEditor: string | null;

  // Task-specific state
  taskViewState: Record<
    string,
    {
      view: "doc" | "chats" | "activity";
      activeChatId: string | null;
      openChatIds: string[];
    }
  >;

  // Actions
  setView: (view: "doc" | "chats" | "kanban") => void;
  setActiveChatId: (chatId: string | null) => void;
  addOpenChat: (chatId: string) => void;
  removeOpenChat: (chatId: string) => void;
  setContextWidth: (width: number) => void;
  setLastFocusedEditor: (editorId: string | null) => void;
  setTaskViewState: (
    taskId: string,
    state: {
      view: "doc" | "chats" | "activity";
      activeChatId: string | null;
      openChatIds: string[];
    }
  ) => void;
  resetTaskViewState: (taskId: string) => void;
}

export const useWorkroomStore = create<WorkroomState>()(
  persist(
    (set) => ({
      view: "kanban",
      openChatIds: [],
      activeChatId: null,
      contextWidth: 300,
      lastFocusedEditor: null,
      taskViewState: {},

      setView: (view) => set({ view }),
      setActiveChatId: (activeChatId) => set({ activeChatId }),
      addOpenChat: (chatId) =>
        set((state) => ({
          openChatIds: state.openChatIds.includes(chatId)
            ? state.openChatIds
            : [...state.openChatIds, chatId],
        })),
      removeOpenChat: (chatId) =>
        set((state) => ({
          openChatIds: state.openChatIds.filter((id) => id !== chatId),
          activeChatId:
            state.activeChatId === chatId ? null : state.activeChatId,
        })),
      setContextWidth: (contextWidth) => set({ contextWidth }),
      setLastFocusedEditor: (lastFocusedEditor) => set({ lastFocusedEditor }),
      setTaskViewState: (taskId, state) =>
        set((store) => ({
          taskViewState: {
            ...store.taskViewState,
            [taskId]: state,
          },
        })),
      resetTaskViewState: (taskId) =>
        set((store) => {
          const { [taskId]: _, ...rest } = store.taskViewState;
          return { taskViewState: rest };
        }),
    }),
    {
      name: "workroom-storage",
      storage: isClient ? createJSONStorage(() => localStorage) : undefined,
    }
  )
);


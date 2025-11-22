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
  priority_pin?: boolean;
  due?: string;
  tags?: string[];
  microNote?: string;
  doc?: TaskDoc;
  chats: ChatMeta[];
  unreadCount?: number;
  createdAt: string;
  updatedAt: string;
}

export type Mode = "manage" | "do";
export type Level = "global" | "project" | "task";
export type View = "doc" | "chats" | "activity" | "kanban";
export type PrimaryView = "workroom" | "kanban";

export interface WorkroomState {
  // Hydration state
  hydrated: boolean;

  // Mode and level
  mode: Mode;
  level: Level;

  // Selection state
  projectId: string | undefined;
  taskId: string | undefined;

  // View state
  view: View;
  lastViewPerTask: Record<string, Exclude<View, "kanban">>;
  primaryView: PrimaryView;

  // Pane state
  navOpen: boolean; // respected only in non-kanban
  contextOpen: boolean; // respected only in task views

  // Legacy state (kept for compatibility)
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
  openProject: (projectId?: string) => void;
  openTask: (
    projectId: string,
    taskId: string,
    view?: Exclude<View, "kanban">
  ) => void;
  setProject: (projectId?: string) => void;
  setTask: (taskId?: string) => void;
  setView: (view: View) => void;
  setNavOpen: (open: boolean) => void;
  setContextOpen: (open: boolean) => void;
  setPrimaryView: (view: PrimaryView) => void;
  openNav: () => void;
  closeNav: () => void;
  toggleNav: () => void;
  openContext: () => void;
  closeContext: () => void;
  toggleContext: () => void;
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
    (set, get) => ({
      hydrated: false,
      mode: "do",
      level: "global",
      projectId: undefined,
      taskId: undefined,
      view: "chats",
      lastViewPerTask: {},
      primaryView: "workroom",
      navOpen: true,
      contextOpen: false,
      openChatIds: [],
      activeChatId: null,
      contextWidth: 300,
      lastFocusedEditor: null,
      taskViewState: {},

      openProject: (projectId) =>
        set({
          projectId,
          taskId: undefined,
          level: projectId ? "project" : "global",
          mode: "manage",
          view: "kanban",
          primaryView: "kanban",
          contextOpen: false,
          navOpen: false,
        }),

      openTask: (projectId, taskId, view) =>
        set((state) => {
          const nextView = view ?? state.lastViewPerTask[taskId] ?? "chats";
          return {
            projectId,
            taskId,
            level: "task",
            mode: "do",
            view: nextView,
            primaryView: "workroom",
            contextOpen: true,
            lastViewPerTask: {
              ...state.lastViewPerTask,
              [taskId]: nextView,
            },
            navOpen: true,
          };
        }),

      setProject: (projectId) =>
        set((state) => ({
          projectId,
          taskId: undefined,
          level: projectId ? "project" : "global",
          mode: "manage",
          view: "kanban",
          primaryView: "kanban",
          // context/nav ignored in kanban, keep previous values to restore later
          contextOpen: state.contextOpen,
          navOpen: true,
        })),

      setTask: (taskId) => {
        const { projectId } = get();
        if (!taskId || !projectId) {
          return set({
            taskId: undefined,
            level: projectId ? "project" : "global",
            mode: "manage",
            view: "kanban",
            primaryView: "kanban",
            contextOpen: false,
            navOpen: false,
          });
        }
        get().openTask(projectId, taskId);
      },

      setView: (view) =>
        set((state) => {
          const newState: Partial<WorkroomState> = {
            view,
            mode: view === "kanban" ? "manage" : "do",
            // in non-kanban, open context if level === task
            contextOpen:
              view === "kanban"
                ? state.contextOpen
                : state.level === "task"
                ? true
                : false,
          };
          if (view === "kanban") {
            newState.primaryView = "kanban";
            newState.navOpen = false;
            newState.taskId = undefined;
            newState.level = state.projectId ? "project" : "global";
          } else {
            newState.primaryView = "workroom";
            newState.navOpen = true;
            const tv = state.taskId ? view : "chats";
            newState.view = tv;
            if (state.taskId) {
              newState.lastViewPerTask = {
                ...state.lastViewPerTask,
                [state.taskId]: tv as Exclude<View, "kanban">,
              };
            }
          }
          return newState;
        }),
      setPrimaryView: (primaryView) =>
        set((state) => {
          if (primaryView === "kanban") {
            return {
              primaryView,
              mode: "manage",
              view: "kanban",
              contextOpen: false,
              navOpen: false,
              level: state.projectId ? "project" : "global",
            };
          }
          return {
            primaryView,
            mode: "do",
            contextOpen: !!state.taskId,
            navOpen: true,
          };
        }),
      setNavOpen: (navOpen) => set({ navOpen }),
      setContextOpen: (contextOpen) => set({ contextOpen }),
      openNav: () => set({ navOpen: true }),
      closeNav: () => set({ navOpen: false }),
      toggleNav: () => set((state) => ({ navOpen: !state.navOpen })),
      openContext: () => set({ contextOpen: true }),
      closeContext: () => set({ contextOpen: false }),
      toggleContext: () =>
        set((state) => ({ contextOpen: !state.contextOpen })),
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
      onRehydrateStorage: () => {
        return (state, error) => {
          if (!error) {
            // Set hydrated flag after rehydration completes, regardless of whether
            // state exists (first-time load will have undefined state)
            setTimeout(() => {
              useWorkroomStore.setState({ hydrated: true });
            }, 0);
          }
        };
      },
    }
  )
);

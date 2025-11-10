import { useState, useEffect } from "react";
import { TaskDoc } from "./TaskDoc";
import { ThreadView } from "./ThreadView";
import { ChatTabs } from "./ChatTabs";
import { ActivityList } from "./ActivityList";
import { useWorkroomStore } from "../../hooks/useWorkroomStore";
import { workroomApi } from "../../lib/workroomApi";
import type { Task, ChatMeta, View } from "../../hooks/useWorkroomStore";
import { Text } from "@ygt-assistant/ui";
import { Link24Regular, Add24Regular } from "@fluentui/react-icons";

interface WorkspaceProps {
  taskId: string;
  projectId: string;
  projectTitle?: string;
}

export function Workspace({ taskId }: WorkspaceProps) {
  const {
    view,
    setView,
    taskViewState,
    setTaskViewState,
    hydrated,
    openContext,
  } = useWorkroomStore();
  const [task, setTask] = useState<Task | null>(null);
  const [loading, setLoading] = useState(true);
  const [chats, setChats] = useState<ChatMeta[]>([]);

  if (!hydrated) {
    return <div className="p-4" />;
  }

  if (!taskId) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <Text variant="muted" className="text-sm mb-2">
            Select a task to view
          </Text>
          <Text variant="caption" className="text-xs text-slate-500">
            Use Navigator or press ⌘K to search
          </Text>
        </div>
      </div>
    );
  }

  const taskState = taskViewState[taskId] || {
    view: "chats",
    activeChatId: null,
    openChatIds: [],
  };

  // Use global view (never render kanban inside Workspace center pane)
  const activeView: View = view === "kanban" ? "chats" : view;

  const loadTask = async () => {
    try {
      setLoading(true);
      const response = await workroomApi.getTask(taskId);
      if (response.ok) {
        setTask(response.task);
        setChats(response.task.chats || []);
      }
    } catch (err) {
      console.error("Failed to load task:", err);
    } finally {
      setLoading(false);
    }
  };

  const loadChats = async () => {
    try {
      const response = await workroomApi.getChats(taskId);
      if (response.ok) {
        setChats(response.chats);
      }
    } catch (err) {
      console.error("Failed to load chats:", err);
    }
  };

  useEffect(() => {
    if (taskId) {
      loadTask();
      loadChats();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [taskId]);

  const handleViewChange = (newView: View) => {
    if (newView === "kanban") {
      setView("kanban");
      return;
    }
    setTaskViewState(taskId, { ...taskState, view: newView });
    setView(newView);
  };

  const handleChatSelect = (chatId: string) => {
    if (typeof window === "undefined") return;

    setTaskViewState(taskId, {
      ...taskState,
      activeChatId: chatId,
      view: "chats",
      openChatIds: taskState.openChatIds.includes(chatId)
        ? taskState.openChatIds
        : [...taskState.openChatIds, chatId],
    });
    setView("chats");
  };

  const handleAttachSource = () => {
    openContext();
    // TODO: Focus Search tab in ContextPane
  };

  if (loading) {
    return <div className="p-4">Loading...</div>;
  }

  if (!task) {
    return <div className="p-4">Task not found</div>;
  }

  const tabs: Array<{ id: View; label: string }> = [
    { id: "doc", label: "Task" },
    { id: "chats", label: "Chats" },
    { id: "activity", label: "Activity" },
  ];

  return (
    <div className="flex flex-col flex-1 min-w-0 min-h-0">
      {/* Tabs Row */}
      <div className="px-4 pt-3 pb-0 border-b border-slate-200">
        <div className="flex items-center gap-1">
          {tabs.map((tab) => {
            const isActive = activeView === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => handleViewChange(tab.id)}
                className={`relative px-3 py-2 text-sm font-medium transition-colors ${
                  isActive
                    ? "text-slate-900"
                    : "text-slate-600 hover:text-slate-900"
                }`}
                aria-selected={isActive}
                aria-controls={`workroom-${tab.id}`}
              >
                {tab.label}
                {isActive && (
                  <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-sky-500 transition-all duration-120 ease-in-out" />
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Breadcrumb & Actions Row */}
      <div className="px-4 py-3 flex items-center justify-between border-b border-slate-200">
        <Text variant="caption" className="text-xs text-slate-500">
          Context — Task: {task.title}
        </Text>
        <div className="flex items-center gap-2">
          <button
            onClick={handleAttachSource}
            className="inline-flex items-center gap-1 px-2 py-1 text-xs text-slate-600 hover:text-slate-900 hover:bg-slate-50 rounded transition-colors"
            title="Attach source"
          >
            <Link24Regular className="w-3.5 h-3.5" />
            Attach source
          </button>
          <button
            className="inline-flex items-center gap-1 px-2 py-1 text-xs text-slate-600 hover:text-slate-900 hover:bg-slate-50 rounded transition-colors"
            title="Add focus block"
          >
            <Add24Regular className="w-3.5 h-3.5" />
            Add focus block
          </button>
          <select
            className="text-xs text-slate-600 border border-slate-200 rounded px-2 py-1 bg-white hover:bg-slate-50 transition-colors"
            value={task.status}
            onChange={(e) => {
              // TODO: Update task status
            }}
          >
            <option value="backlog">Backlog</option>
            <option value="ready">Ready</option>
            <option value="doing">Doing</option>
            <option value="blocked">Blocked</option>
            <option value="done">Done</option>
          </select>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden min-w-0">
        {activeView === "doc" && (
          <TaskDoc
            taskId={taskId}
            initialContent={task.doc?.contentJSON}
            onContentChange={async (contentJSON) => {
              // Auto-save handled in TaskDoc
            }}
          />
        )}

        {activeView === "chats" && (
          <div className="flex-1 flex flex-col min-h-0">
            <ChatTabs
              chats={chats}
              activeChatId={taskState.activeChatId}
              onSelectChat={handleChatSelect}
              onCloseChat={(chatId) => {
                const newOpenChats = taskState.openChatIds.filter(
                  (id) => id !== chatId
                );
                setTaskViewState(taskId, {
                  ...taskState,
                  openChatIds: newOpenChats,
                  activeChatId:
                    taskState.activeChatId === chatId
                      ? newOpenChats[0] || null
                      : taskState.activeChatId,
                });
              }}
              onCreateChat={async () => {
                try {
                  const response = await workroomApi.createChat(taskId, {
                    title: `Chat ${chats.length + 1}`,
                  });
                  if (response.ok) {
                    await loadChats();
                    handleChatSelect(response.chat.id);
                  }
                } catch (err) {
                  console.error("Failed to create chat:", err);
                }
              }}
            />
            {taskState.activeChatId ? (
              <ThreadView
                threadId={taskState.activeChatId}
                taskId={taskId}
                mode="workroom"
              />
            ) : (
              <div className="flex-1 flex items-center justify-center p-4">
                <div className="border-2 border-dashed border-slate-300 rounded-lg p-6 text-center max-w-md">
                  <Text variant="muted" className="text-sm mb-2">
                    No chat selected
                  </Text>
                  <Text variant="caption" className="text-xs text-slate-500">
                    Select a chat from the tabs above or create a new one
                  </Text>
                </div>
              </div>
            )}
          </div>
        )}

        {activeView === "activity" && <ActivityList taskId={taskId} />}
      </div>
    </div>
  );
}

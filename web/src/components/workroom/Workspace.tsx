import { useState, useEffect } from "react";
import { useRouter } from "next/router";
import { TaskDoc } from "./TaskDoc";
import { ThreadView } from "./ThreadView";
import { ChatTabs } from "./ChatTabs";
import { ContextPane } from "./ContextPane";
import { useWorkroomStore } from "../../hooks/useWorkroomStore";
import { workroomApi } from "../../lib/workroomApi";
import type { Task, ChatMeta, TaskDoc as TaskDocType } from "../../hooks/useWorkroomStore";
import { Button } from "@ygt-assistant/ui";
import {
  Document24Regular,
  Chat24Regular,
  History24Regular,
} from "@fluentui/react-icons";

interface WorkspaceProps {
  taskId: string;
  projectId: string;
}

export function Workspace({ taskId, projectId }: WorkspaceProps) {
  const router = useRouter();
  const { taskViewState, setTaskViewState } = useWorkroomStore();
  const [task, setTask] = useState<Task | null>(null);
  const [loading, setLoading] = useState(true);
  const [chats, setChats] = useState<ChatMeta[]>([]);

  const taskState = taskViewState[taskId] || {
    view: "doc",
    activeChatId: null,
    openChatIds: [],
  };

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

  const handleViewChange = (view: "doc" | "chats" | "activity") => {
    setTaskViewState(taskId, {
      ...taskState,
      view,
    });
    router.replace({
      pathname: router.pathname,
      query: { ...router.query, view },
    });
  };

  const handleChatSelect = (chatId: string) => {
    setTaskViewState(taskId, {
      ...taskState,
      activeChatId: chatId,
      view: "chats",
      openChatIds: taskState.openChatIds.includes(chatId)
        ? taskState.openChatIds
        : [...taskState.openChatIds, chatId],
    });
    router.replace({
      pathname: router.pathname,
      query: { ...router.query, view: "chats", chatId },
    });
  };

  if (loading) {
    return <div className="p-4">Loading...</div>;
  }

  if (!task) {
    return <div className="p-4">Task not found</div>;
  }

  return (
    <div className="flex flex-col h-full">
      {/* Tabs */}
      <div className="flex border-b border-slate-200">
        <button
          onClick={() => handleViewChange("doc")}
          className={`flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            taskState.view === "doc"
              ? "border-blue-500 text-blue-600"
              : "border-transparent text-slate-600 hover:text-slate-900"
          }`}
        >
          <Document24Regular className="w-4 h-4" />
          Doc
        </button>
        <button
          onClick={() => handleViewChange("chats")}
          className={`flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            taskState.view === "chats"
              ? "border-blue-500 text-blue-600"
              : "border-transparent text-slate-600 hover:text-slate-900"
          }`}
        >
          <Chat24Regular className="w-4 h-4" />
          Chats ({task.chats.length})
        </button>
        <button
          onClick={() => handleViewChange("activity")}
          className={`flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            taskState.view === "activity"
              ? "border-blue-500 text-blue-600"
              : "border-transparent text-slate-600 hover:text-slate-900"
          }`}
        >
          <History24Regular className="w-4 h-4" />
          Activity
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 flex overflow-hidden">
        <div className="flex-1 overflow-hidden">
          {taskState.view === "doc" && (
            <TaskDoc
              taskId={taskId}
              initialContent={task.doc?.contentJSON}
              onContentChange={async (contentJSON) => {
                // Auto-save handled in TaskDoc
              }}
            />
          )}

          {taskState.view === "chats" && (
            <div className="h-full flex flex-col">
              <ChatTabs
                chats={chats}
                activeChatId={taskState.activeChatId}
                onSelectChat={handleChatSelect}
                onCloseChat={(chatId) => {
                  const newOpenChats = taskState.openChatIds.filter((id) => id !== chatId);
                  setTaskViewState(taskId, {
                    ...taskState,
                    openChatIds: newOpenChats,
                    activeChatId: taskState.activeChatId === chatId ? newOpenChats[0] || null : taskState.activeChatId,
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
                <div className="p-4 text-center text-slate-500">
                  Select a chat or create a new one
                </div>
              )}
            </div>
          )}

          {taskState.view === "activity" && (
            <div className="p-4">
              <div className="text-sm text-slate-600">
                Activity log coming soon
              </div>
            </div>
          )}
        </div>

        {/* Context Pane */}
        <ContextPane taskId={taskId} />
      </div>
    </div>
  );
}


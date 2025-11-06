import { useState } from "react";
import { Text } from "@ygt-assistant/ui";
import type { Task, TaskStatus } from "../../hooks/useWorkroomStore";

interface KanbanBoardProps {
  tasks: Task[];
  onUpdateTaskStatus: (taskId: string, status: TaskStatus) => void;
  onSelectTask: (taskId: string) => void;
}

const statusColumns: { id: TaskStatus; label: string }[] = [
  { id: "backlog", label: "Backlog" },
  { id: "ready", label: "Ready" },
  { id: "doing", label: "Doing" },
  { id: "blocked", label: "Blocked" },
  { id: "done", label: "Done" },
];

export function KanbanBoard({
  tasks,
  onUpdateTaskStatus,
  onSelectTask,
}: KanbanBoardProps) {
  const [draggedTaskId, setDraggedTaskId] = useState<string | null>(null);

  const tasksByStatus = {
    backlog: tasks.filter((t) => t.status === "backlog"),
    ready: tasks.filter((t) => t.status === "ready"),
    doing: tasks.filter((t) => t.status === "doing"),
    blocked: tasks.filter((t) => t.status === "blocked"),
    done: tasks.filter((t) => t.status === "done"),
  };

  const handleDragStart = (taskId: string) => {
    setDraggedTaskId(taskId);
  };

  const handleDragOver = (e: React.DragEvent, status: TaskStatus) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent, status: TaskStatus) => {
    e.preventDefault();
    if (draggedTaskId) {
      onUpdateTaskStatus(draggedTaskId, status);
      setDraggedTaskId(null);
    }
  };

  const getDocExcerpt = (task: Task): string => {
    if (!task.doc?.contentJSON) return "";
    // Extract text from TipTap JSON (simplified)
    const content = task.doc.contentJSON.content || [];
    const text = content
      .map((node: any) => {
        if (node.type === "paragraph" && node.content) {
          return node.content
            .map((c: any) => c.text || "")
            .join("")
            .slice(0, 100);
        }
        return "";
      })
      .join(" ")
      .trim();
    return text || "";
  };

  const getLastEmbedStatus = (task: Task): string | null => {
    // TODO: Fetch from messages/embeds
    return null;
  };

  return (
    <div className="h-full overflow-x-auto">
      <div className="flex gap-4 min-w-max p-4">
        {statusColumns.map((column) => {
          const columnTasks = tasksByStatus[column.id];
          return (
            <div
              key={column.id}
              className="flex-shrink-0 w-64 border rounded-lg bg-slate-50"
              onDragOver={(e) => handleDragOver(e, column.id)}
              onDrop={(e) => handleDrop(e, column.id)}
            >
              <div className="p-3 border-b bg-white rounded-t-lg">
                <div className="text-sm font-medium text-slate-900">
                  {column.label}
                </div>
                <div className="text-xs text-slate-500 mt-1">
                  {columnTasks.length} task{columnTasks.length !== 1 ? "s" : ""}
                </div>
              </div>
              <div className="p-2 space-y-2 min-h-[200px]">
                {columnTasks.map((task) => {
                  const excerpt = getDocExcerpt(task);
                  const embedStatus = getLastEmbedStatus(task);
                  return (
                    <div
                      key={task.id}
                      draggable
                      onDragStart={() => handleDragStart(task.id)}
                      onClick={() => onSelectTask(task.id)}
                      className="bg-white border rounded p-3 cursor-pointer hover:shadow-md transition-shadow"
                    >
                      <div className="flex items-start justify-between gap-2 mb-2">
                        <Text variant="body" className="text-sm font-medium">
                          {task.title}
                        </Text>
                        {task.unreadCount && task.unreadCount > 0 && (
                          <span className="flex-shrink-0 bg-blue-500 text-white text-xs rounded-full px-2 py-0.5">
                            {task.unreadCount}
                          </span>
                        )}
                      </div>
                      {excerpt && (
                        <Text variant="caption" className="text-xs text-slate-600 line-clamp-2">
                          {excerpt}
                        </Text>
                      )}
                      {embedStatus && (
                        <div className="mt-2">
                          <span className="text-xs px-2 py-0.5 bg-blue-100 text-blue-800 rounded">
                            {embedStatus}
                          </span>
                        </div>
                      )}
                      {task.chats.length > 0 && (
                        <div className="mt-2 text-xs text-slate-500">
                          {task.chats.length} chat{task.chats.length !== 1 ? "s" : ""}
                        </div>
                      )}
                    </div>
                  );
                })}
                {columnTasks.length === 0 && (
                  <div className="text-xs text-slate-400 text-center py-8">
                    No tasks
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}


import { useMemo, useState } from "react";
import { Text } from "@lucid-work/ui";
import { useFocusContextStore } from "../../state/focusContextStore";
import type { FocusAnchor } from "../../lib/focusContext";
import type { Task, TaskStatus } from "../../hooks/useWorkroomStore";
import { getMockTasks, statusLabelMap, updateMockTaskStatus } from "../../data/mockWorkroomData";
import { workroomApi } from "../../lib/workroomApi";

type BoardColumn = {
  key: TaskStatus;
  title: string;
};

const columns: BoardColumn[] = [
  { key: "backlog", title: "Backlog" },
  { key: "ready", title: "Ready" },
  { key: "doing", title: "Doing" },
  { key: "blocked", title: "Blocked" },
  { key: "done", title: "Done" },
];

interface WorkBoardProps {
  boardType: "portfolio" | "project";
  anchor: FocusAnchor;
}

export function WorkBoard({ boardType, anchor }: WorkBoardProps) {
  const [tasks, setTasks] = useState<Task[]>(getMockTasks());
  const [draggingId, setDraggingId] = useState<string | null>(null);
  const { pushFocus } = useFocusContextStore();

  const visibleTasks = useMemo(() => {
    if (boardType === "project" && anchor.id) {
      return tasks.filter((task) => task.projectId === anchor.id);
    }
    return tasks;
  }, [tasks, boardType, anchor.id]);

  const handleDrop = async (status: BoardColumn["key"], taskId: string) => {
    let previousStatus: TaskStatus | undefined;
    setTasks((prev) =>
      prev.map((task) => {
        if (task.id === taskId) {
          previousStatus = task.status as TaskStatus;
          return { ...task, status };
        }
        return task;
      })
    );
    try {
      await workroomApi.updateTaskStatus(taskId, status);
      updateMockTaskStatus(taskId, status);
    } catch (err) {
      setTasks((prev) =>
        prev.map((task) => (task.id === taskId ? { ...task, status: previousStatus ?? task.status } : task))
      );
      // eslint-disable-next-line no-console
      console.error("Failed to update task status", err);
    }
  };

  const onCardClick = (task: Task) => {
    const surfaceKind =
      boardType === "portfolio" && anchor.id === "my_work"
        ? "my_work"
        : "project_board";
    pushFocus({ type: "task", id: task.id }, { source: "board", surfaceKind });
  };

  return (
    <div className="flex h-full flex-col gap-4 p-4">
      <div className="flex items-center justify-between">
        <div>
          <Text variant="caption" className="text-xs uppercase text-slate-500">
            {boardType === "portfolio" ? "Portfolio" : "Project"}
          </Text>
          <Text variant="body" className="text-lg font-semibold">
            {boardType === "portfolio" && anchor.id === "my_work"
              ? "My Work"
              : anchor.id || "Board"}
          </Text>
        </div>
        <Text variant="caption" className="text-xs text-slate-500">
          Drag cards to update their status
        </Text>
      </div>
      <div className="grid flex-1 grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-5">
        {columns.map((column) => (
          <div
            key={column.key}
            className="flex flex-col rounded-lg border border-slate-200 bg-slate-50"
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault();
              const taskId = e.dataTransfer.getData("text/plain");
              if (taskId) {
                handleDrop(column.key, taskId);
              }
              setDraggingId(null);
            }}
          >
            <div className="border-b border-slate-200 px-3 py-2 text-sm font-semibold text-slate-700">
              {column.title}
            </div>
            <div className="flex flex-1 flex-col gap-2 p-3">
              {visibleTasks
                .filter((task) => task.status === column.key)
                .map((task) => (
                  <div
                    key={task.id}
                    draggable
                    onDragStart={(e) => {
                      setDraggingId(task.id);
                      e.dataTransfer.setData("text/plain", task.id);
                    }}
                    onDragEnd={() => setDraggingId(null)}
                    onClick={() => onCardClick(task)}
                    className={`cursor-pointer rounded-lg border bg-white p-3 text-sm shadow-sm transition hover:shadow-md ${
                      draggingId === task.id ? "opacity-60" : ""
                    }`}
                  >
                    <div className="font-semibold text-slate-800">{task.title}</div>
                    <div className="text-xs text-slate-500">
                      Status: {statusLabelMap[task.status as TaskStatus] || task.status}
                    </div>
                  </div>
                ))}
              {visibleTasks.filter((task) => task.status === column.key).length === 0 && (
                <div className="rounded border border-dashed border-slate-200 p-3 text-center text-xs text-slate-400">
                  No tasks
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

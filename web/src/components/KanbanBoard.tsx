import { useState } from "react";
import { Text, Button } from "@ygt-assistant/ui";

interface Project {
  id: string;
  name: string;
  children: Task[];
}

interface Task {
  id: string;
  project_id: string;
  title: string;
  status: "todo" | "doing" | "done" | "blocked";
  importance: string;
  children: Thread[];
}

interface Thread {
  id: string;
  task_id: string;
  title: string;
}

interface KanbanBoardProps {
  projects: Project[];
  onUpdateTaskStatus: (taskId: string, status: string) => void;
  onSelectTask?: (taskId: string) => void;
}

const statusColumns = [
  { id: "todo", label: "To Do" },
  { id: "doing", label: "Doing" },
  { id: "done", label: "Done" },
  { id: "blocked", label: "Blocked" },
];

export function KanbanBoard({ projects, onUpdateTaskStatus, onSelectTask }: KanbanBoardProps) {
  // Flatten all tasks from all projects
  const allTasks: Task[] = (projects || []).flatMap((project) => project.children || []);

  // Group tasks by status
  const tasksByStatus = {
    todo: allTasks.filter((t) => t.status === "todo"),
    doing: allTasks.filter((t) => t.status === "doing"),
    done: allTasks.filter((t) => t.status === "done"),
    blocked: allTasks.filter((t) => t.status === "blocked"),
  };

  return (
    <div className="rounded-lg border p-4">
      <div className="text-sm font-medium mb-4">Kanban Board</div>
      <div className="grid grid-cols-4 gap-4">
        {statusColumns.map((column) => (
          <div key={column.id} className="border rounded p-3">
            <div className="text-xs font-medium mb-2">
              {column.label} ({tasksByStatus[column.id as keyof typeof tasksByStatus].length})
            </div>
            <div className="space-y-2">
              {tasksByStatus[column.id as keyof typeof tasksByStatus].map((task) => {
                const project = (projects || []).find((p) => p.id === task.project_id);
                return (
                  <div
                    key={task.id}
                    className="border rounded p-2 bg-white hover:shadow-sm cursor-pointer"
                    onClick={() => {
                      if (onSelectTask) {
                        onSelectTask(task.id);
                      } else {
                        console.log("Open task:", task.id);
                      }
                    }}
                  >
                    <div className="text-xs font-medium">{task.title}</div>
                    {project && (
                      <div className="text-xs text-gray-500 mt-1">
                        {project.name}
                      </div>
                    )}
                    <div className="text-xs text-gray-400 mt-1">
                      {task.children?.length || 0} thread{(task.children?.length || 0) !== 1 ? "s" : ""}
                    </div>
                  </div>
                );
              })}
              {tasksByStatus[column.id as keyof typeof tasksByStatus].length === 0 && (
                <div className="text-xs text-gray-400 text-center py-4">
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

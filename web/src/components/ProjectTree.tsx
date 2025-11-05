import { useState } from "react";
import { Button, Stack, Text } from "@lucid-work/ui";

interface Project {
  id: string;
  name: string;
  description?: string;
  priority: string;
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
  messages: any[];
}

interface ProjectTreeProps {
  projects: Project[];
  onSelectThread: (thread: Thread) => void;
  onCreateThread?: (taskId: string, title: string) => void;
  selectedThreadId?: string | null;
}

export function ProjectTree({
  projects,
  onSelectThread,
  onCreateThread,
  selectedThreadId,
}: ProjectTreeProps) {
  const [expandedProjects, setExpandedProjects] = useState<Set<string>>(
    new Set((projects || []).map((p) => p.id))
  );
  const [expandedTasks, setExpandedTasks] = useState<Set<string>>(new Set());
  const [newThreadInput, setNewThreadInput] = useState<Record<string, string>>(
    {}
  );

  const toggleProject = (projectId: string) => {
    const newExpanded = new Set(expandedProjects);
    if (newExpanded.has(projectId)) {
      newExpanded.delete(projectId);
    } else {
      newExpanded.add(projectId);
    }
    setExpandedProjects(newExpanded);
  };

  const toggleTask = (taskId: string) => {
    const newExpanded = new Set(expandedTasks);
    if (newExpanded.has(taskId)) {
      newExpanded.delete(taskId);
    } else {
      newExpanded.add(taskId);
    }
    setExpandedTasks(newExpanded);
  };

  const handleNewThreadSubmit = (taskId: string) => {
    if (newThreadInput[taskId] && onCreateThread) {
      onCreateThread(taskId, newThreadInput[taskId]);
      setNewThreadInput((prev) => ({ ...prev, [taskId]: "" }));
    }
  };

  return (
    <div className="rounded-lg border p-4 space-y-2">
      <div className="text-sm font-medium mb-3">Projects</div>
      {!projects || projects.length === 0 ? (
        <Text variant="muted" className="text-xs">
          No projects yet
        </Text>
      ) : (
        projects.map((project) => (
          <div key={project.id} className="space-y-1">
            <div
              className="flex items-center justify-between cursor-pointer hover:bg-gray-50 p-1 rounded"
              onClick={() => toggleProject(project.id)}
            >
              <span className="text-sm font-medium">{project.name}</span>
              <span className="text-xs text-gray-500">
                {expandedProjects.has(project.id) ? "−" : "+"}
              </span>
            </div>
            {expandedProjects.has(project.id) && (
              <div className="ml-4 space-y-1">
                {project.children.map((task) => (
                  <div key={task.id} className="space-y-1">
                    <div
                      className="flex items-center justify-between cursor-pointer hover:bg-gray-50 p-1 rounded"
                      onClick={() => toggleTask(task.id)}
                    >
                      <span className="text-xs">{task.title}</span>
                      <span className="text-xs text-gray-400">
                        {expandedTasks.has(task.id) ? "−" : "+"}
                      </span>
                    </div>
                    {expandedTasks.has(task.id) && (
                      <div className="ml-4 space-y-1">
                        {task.children.map((thread) => (
                          <div
                            key={thread.id}
                            className={`text-xs p-1 rounded cursor-pointer hover:bg-gray-50 ${
                              selectedThreadId === thread.id
                                ? "bg-blue-50 border border-blue-200"
                                : ""
                            }`}
                            onClick={() => onSelectThread(thread)}
                          >
                            {thread.title}
                          </div>
                        ))}
                        {onCreateThread && (
                          <div className="flex items-center gap-1 mt-1">
                            <input
                              type="text"
                              placeholder="New thread..."
                              value={newThreadInput[task.id] || ""}
                              onChange={(e) =>
                                setNewThreadInput((prev) => ({
                                  ...prev,
                                  [task.id]: e.target.value,
                                }))
                              }
                              onKeyPress={(e) => {
                                if (e.key === "Enter") {
                                  handleNewThreadSubmit(task.id);
                                }
                              }}
                              className="text-xs border rounded px-2 py-1 flex-1"
                            />
                            <button
                              className="text-xs text-blue-600 hover:text-blue-800 p-1"
                              onClick={() => handleNewThreadSubmit(task.id)}
                            >
                              +
                            </button>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        ))
      )}
    </div>
  );
}

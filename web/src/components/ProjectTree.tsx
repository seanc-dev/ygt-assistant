import { useState } from "react";
import { Button, Stack, Text } from "@ygt-assistant/ui";

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
  tree: Project[];
  onThreadSelect: (thread: Thread) => void;
  selectedThreadId?: string | null;
}

export function ProjectTree({
  tree,
  onThreadSelect,
  selectedThreadId,
}: ProjectTreeProps) {
  const [expandedProjects, setExpandedProjects] = useState<Set<string>>(
    new Set(tree.map((p) => p.id))
  );
  const [expandedTasks, setExpandedTasks] = useState<Set<string>>(new Set());

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

  return (
    <div className="rounded-lg border p-4 space-y-2">
      <div className="text-sm font-medium mb-3">Projects</div>
      {tree.length === 0 ? (
        <Text variant="muted" className="text-xs">
          No projects yet
        </Text>
      ) : (
        tree.map((project) => (
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
                            onClick={() => onThreadSelect(thread)}
                          >
                            {thread.title}
                          </div>
                        ))}
                        <button
                          className="text-xs text-blue-600 hover:text-blue-800 p-1"
                          onClick={() => {
                            // TODO: Open create thread dialog
                            console.log("Create thread for task:", task.id);
                          }}
                        >
                          + New thread
                        </button>
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

import { useState, useEffect, useRef, useCallback } from "react";
import {
  ChevronRight24Regular,
  ChevronDown24Regular,
} from "@fluentui/react-icons";
import { Text } from "@ygt-assistant/ui";
import { useWorkroomStore } from "../../hooks/useWorkroomStore";
import type { Project, Task, TaskStatus } from "../../hooks/useWorkroomStore";

interface NavigatorProps {
  open: boolean;
  onClose: () => void;
  projects: Project[];
  tasks: Task[];
  selectedProjectId?: string;
  selectedTaskId?: string;
}

const statusColors: Record<TaskStatus, string> = {
  backlog: "bg-slate-50 text-slate-700",
  ready: "bg-blue-50 text-blue-700",
  doing: "bg-amber-50 text-amber-700",
  blocked: "bg-rose-50 text-rose-700",
  done: "bg-emerald-50 text-emerald-700",
};

export function Navigator({
  open,
  onClose,
  projects,
  tasks,
  selectedProjectId,
  selectedTaskId,
}: NavigatorProps) {
  const { openProject, openTask, closeNav, view } = useWorkroomStore();
  const isKanban = view === "kanban";

  // Project click handler
  const handleProjectClick = (projectId: string) => {
    openProject(projectId);
  };

  // Task click handler
  const handleTaskClick = (projectId: string, taskId: string) => {
    openTask(projectId, taskId);
    // Focus the message input
    if (typeof window !== "undefined") {
      window.dispatchEvent(new CustomEvent("workspace:focus-input"));
    }
  };

  const handleClose = useCallback(() => {
    closeNav();
    onClose();
  }, [closeNav, onClose]);
  const [expandedProjects, setExpandedProjects] = useState<Set<string>>(
    new Set(selectedProjectId ? [selectedProjectId] : [])
  );
  const [searchQuery, setSearchQuery] = useState("");
  const navRef = useRef<HTMLDivElement>(null);

  // Expand selected project on mount
  useEffect(() => {
    if (selectedProjectId) {
      setExpandedProjects((prev) => new Set([...prev, selectedProjectId]));
    }
  }, [selectedProjectId]);

  // Listen for workspace:focus-input event
  useEffect(() => {
    if (typeof window === "undefined") return;

    const handleFocusInput = () => {
      if (open) {
        handleClose();
      }
    };
    window.addEventListener("workspace:focus-input", handleFocusInput);
    return () => {
      window.removeEventListener("workspace:focus-input", handleFocusInput);
    };
  }, [open, handleClose]);

  // Clickaway handler
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (navRef.current && !navRef.current.contains(e.target as Node)) {
        handleClose();
      }
    };
    if (open) {
      document.addEventListener("mousedown", handleClickOutside);
      return () =>
        document.removeEventListener("mousedown", handleClickOutside);
    }
  }, [open, handleClose]);

  const toggleProject = (projectId: string) => {
    setExpandedProjects((prev) => {
      const next = new Set(prev);
      if (next.has(projectId)) {
        next.delete(projectId);
      } else {
        next.add(projectId);
      }
      return next;
    });
  };

  const filteredProjects = projects.filter((p) =>
    p.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const filteredTasks = tasks.filter((t) =>
    t.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Never render in kanban
  if (!open || isKanban) {
    return null;
  }

  return (
    <div
      ref={navRef}
      className="flex-1 flex flex-col border-r border-slate-200 bg-white flex-shrink-0 min-h-0"
      style={{ width: "260px" }}
    >
      {/* Search */}
      <div className="p-2 border-b border-slate-200">
        <input
          type="text"
          placeholder="Search projects..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full px-2 py-1 text-xs border border-slate-300 rounded focus:outline-none focus:ring-1 focus:ring-sky-500"
        />
      </div>

      {/* Projects & Tasks */}
      <div className="flex-1 overflow-y-auto">
        {filteredProjects.length === 0 ? (
          <div className="p-4 text-xs text-slate-500 text-center">
            No projects found
          </div>
        ) : (
          filteredProjects.map((project) => {
            const projectTasks = filteredTasks.filter(
              (t) => t.projectId === project.id
            );
            const isExpanded = expandedProjects.has(project.id);
            const isSelected = project.id === selectedProjectId;

            return (
              <div key={project.id}>
                {/* Project Row */}
                <div
                  className={`flex items-center gap-1 px-3 py-3 text-sm hover:bg-slate-50 relative transition-colors ${
                    isSelected ? "bg-slate-50" : ""
                  }`}
                >
                  {isSelected && (
                    <span className="absolute left-0 top-0 h-full w-0.5 bg-sky-500" />
                  )}
                  <button
                    onClick={() => toggleProject(project.id)}
                    className="text-slate-400 hover:text-slate-600 p-0.5"
                    aria-label={isExpanded ? "Collapse" : "Expand"}
                  >
                    {isExpanded ? (
                      <ChevronDown24Regular className="w-4 h-4" />
                    ) : (
                      <ChevronRight24Regular className="w-4 h-4" />
                    )}
                  </button>
                  <button
                    onClick={() => handleProjectClick(project.id)}
                    className="flex-1 text-left cursor-pointer"
                  >
                    <Text variant="body" className="text-sm font-medium">
                      {project.title}
                    </Text>
                  </button>
                  <span className="text-xs text-slate-500">
                    {projectTasks.length}
                  </span>
                </div>

                {/* Tasks */}
                {isExpanded && (
                  <div className="pl-4">
                    {projectTasks.length === 0 ? (
                      <div className="px-3 py-2 text-xs text-slate-400">
                        No tasks
                      </div>
                    ) : (
                      projectTasks.map((task) => {
                        const isTaskSelected = task.id === selectedTaskId;
                        return (
                          <div
                            key={task.id}
                            className={`flex items-center gap-2 px-3 py-3 text-xs cursor-pointer hover:bg-slate-50 transition-colors ${
                              isTaskSelected ? "bg-sky-50" : ""
                            }`}
                            onClick={() => handleTaskClick(project.id, task.id)}
                            onKeyDown={(e) => {
                              if (e.key === "Enter") {
                                handleTaskClick(project.id, task.id);
                              }
                            }}
                            tabIndex={0}
                          >
                            <div className="flex-1 min-w-0">
                              <Text
                                variant="body"
                                className={`text-xs truncate ${
                                  isTaskSelected ? "font-medium" : ""
                                }`}
                              >
                                {task.title}
                              </Text>
                            </div>
                            <span
                              className={`text-xs px-2 py-0.5 rounded-lg font-medium ${
                                statusColors[task.status]
                              }`}
                            >
                              {task.status}
                            </span>
                            {task.unreadCount && task.unreadCount > 0 && (
                              <span className="flex-shrink-0 bg-blue-500 text-white text-xs rounded-full px-1.5 py-0.5 min-w-[18px] text-center">
                                {task.unreadCount}
                              </span>
                            )}
                          </div>
                        );
                      })
                    )}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

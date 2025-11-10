import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/router";
import { Layout } from "../../components/Layout";
import { Workspace } from "../../components/workroom/Workspace";
import { KanbanBoard } from "../../components/workroom/KanbanBoard";
import { Toolbar } from "../../components/workroom/Toolbar";
import { SlashMenu, type SlashCommand } from "../ui/SlashMenu";
import { useWorkroomStore } from "../../hooks/useWorkroomStore";
import { workroomApi } from "../../lib/workroomApi";
import type { Task, Project } from "../../hooks/useWorkroomStore";
import { Button } from "@ygt-assistant/ui";
import { Heading, Text } from "@ygt-assistant/ui";

export default function WorkroomPage() {
  const router = useRouter();
  const { projectId, taskId, view, chatId } = router.query;
  const { setView, view: currentView } = useWorkroomStore();
  const [projects, setProjects] = useState<Project[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [loading, setLoading] = useState(true);
  const [slashMenuOpen, setSlashMenuOpen] = useState(false);
  const [slashMenuPosition, setSlashMenuPosition] = useState({ top: 0, left: 0 });
  const slashMenuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (projectId && typeof projectId === "string") {
      loadTasks(projectId);
    }
  }, [projectId]);

  useEffect(() => {
    if (taskId && typeof taskId === "string") {
      loadTask(taskId);
    }
  }, [taskId]);

  useEffect(() => {
    if (view && typeof view === "string" && ["doc", "chats", "kanban"].includes(view)) {
      setView(view as "doc" | "chats" | "kanban");
    }
  }, [view, setView]);

  const loadData = async () => {
    try {
      const response = await workroomApi.getProjects();
      if (response.ok) {
        setProjects(response.projects);
      }
    } catch (err) {
      console.error("Failed to load projects:", err);
    } finally {
      setLoading(false);
    }
  };

  const loadTasks = async (projectId: string) => {
    try {
      const response = await workroomApi.getTasks(projectId);
      if (response.ok) {
        setTasks(response.tasks);
      }
    } catch (err) {
      console.error("Failed to load tasks:", err);
    }
  };

  const loadTask = async (taskId: string) => {
    try {
      const response = await workroomApi.getTask(taskId);
      if (response.ok) {
        setSelectedTask(response.task);
      }
    } catch (err) {
      console.error("Failed to load task:", err);
    }
  };

  const handleTaskSelect = (taskId: string) => {
    router.push({
      pathname: "/workroom",
      query: {
        projectId: projectId || projects[0]?.id,
        taskId,
        view: "doc",
      },
    });
  };

  const handleStatusChange = async (taskId: string, status: string) => {
    try {
      await workroomApi.updateTaskStatus(taskId, status);
      await loadTasks(projectId as string);
      if (selectedTask?.id === taskId) {
        await loadTask(taskId);
      }
    } catch (err) {
      console.error("Failed to update task status:", err);
    }
  };

  const handleSlashCommand = (command: SlashCommand) => {
    setSlashMenuOpen(false);
    // TODO: Insert command prompt into active chat or doc
    console.log("Selected command:", command);
  };

  const handleSlashMenuOpen = () => {
    if (slashMenuRef.current) {
      const rect = slashMenuRef.current.getBoundingClientRect();
      setSlashMenuPosition({
        top: rect.bottom + 4,
        left: rect.left,
      });
      setSlashMenuOpen(true);
    }
  };

  // Hotkeys
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const isMac = navigator.platform.toUpperCase().indexOf("MAC") >= 0;
      const modKey = isMac ? e.metaKey : e.ctrlKey;

      // Cmd/Ctrl+K: Command palette
      if (modKey && e.key === "k") {
        e.preventDefault();
        // TODO: Open command palette
      }

      // g p: Projects
      // g t: Tasks
      // g d: Doc tab
      // g c: Chats tab
      // g k: Kanban
      if (modKey && e.key === "g") {
        // Wait for next key
        const handleNextKey = (e2: KeyboardEvent) => {
          if (e2.key === "p") {
            e2.preventDefault();
            // Focus projects
          } else if (e2.key === "t") {
            e2.preventDefault();
            // Focus tasks
          } else if (e2.key === "d") {
            e2.preventDefault();
            if (taskId) {
              router.replace({
                pathname: router.pathname,
                query: { ...router.query, view: "doc" },
              });
            }
          } else if (e2.key === "c") {
            e2.preventDefault();
            if (taskId) {
              router.replace({
                pathname: router.pathname,
                query: { ...router.query, view: "chats" },
              });
            }
          } else if (e2.key === "k") {
            e2.preventDefault();
            router.replace({
              pathname: router.pathname,
              query: { ...router.query, view: "kanban" },
            });
          }
          window.removeEventListener("keydown", handleNextKey);
        };
        window.addEventListener("keydown", handleNextKey);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [router, taskId]);

  if (loading) {
    return (
      <Layout>
        <div className="p-4">Loading workroom...</div>
      </Layout>
    );
  }

  const activeView = (view as string) || currentView || "kanban";

  return (
    <Layout>
      <div className="flex flex-col h-screen">
        <div className="p-4 border-b">
          <Heading as="h1" variant="display">
            Workroom
          </Heading>
          <Text variant="muted">
            Focused workspace with Task Docs, Chats, and Kanban
          </Text>
        </div>

        {activeView === "kanban" ? (
          <div className="flex-1 overflow-hidden">
            <KanbanBoard
              tasks={tasks}
              onUpdateTaskStatus={handleStatusChange}
              onSelectTask={handleTaskSelect}
            />
          </div>
        ) : selectedTask ? (
          <div className="flex flex-col flex-1 overflow-hidden">
            <Toolbar
              taskId={selectedTask.id}
              status={selectedTask.status}
              onStatusChange={(status) =>
                handleStatusChange(selectedTask.id, status)
              }
              onSlashMenuOpen={handleSlashMenuOpen}
            />
            <div className="flex-1 overflow-hidden">
              <Workspace
                taskId={selectedTask.id}
                projectId={selectedTask.projectId}
              />
            </div>
          </div>
        ) : (
          <div className="p-4 text-center text-slate-500">
            Select a task to view
          </div>
        )}

        {/* Slash Menu */}
        {slashMenuOpen && (
          <div className="relative" ref={slashMenuRef}>
            <SlashMenu
              onSelect={handleSlashCommand}
              onClose={() => setSlashMenuOpen(false)}
              position={slashMenuPosition}
            />
          </div>
        )}
      </div>
    </Layout>
  );
}

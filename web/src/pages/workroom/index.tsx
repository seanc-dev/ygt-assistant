import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/router";
import { Layout } from "../../components/Layout";
import { Navigator } from "../../components/workroom/Navigator";
import { Workspace } from "../../components/workroom/Workspace";
import { ContextPane } from "../../components/workroom/ContextPane";
import { KanbanBoard } from "../../components/workroom/KanbanBoard";
import { WorkroomHeader } from "../../components/workroom/WorkroomHeader";
import { EdgeToggle } from "../../components/workroom/EdgeToggle";
import {
  useWorkroomStore,
  type Mode,
  type Level,
  type View,
  type PrimaryView,
  type Task,
  type Project,
} from "../../hooks/useWorkroomStore";
import { workroomApi } from "../../lib/workroomApi";
import { buildApiUrl } from "../../lib/apiBase";
import { Button } from "@ygt-assistant/ui/primitives/Button";
import { Text } from "@ygt-assistant/ui";
import {
  PanelLeft24Regular,
  ChevronLeft24Regular,
} from "@fluentui/react-icons";

export default function WorkroomPage() {
  const router = useRouter();
  const {
    level: urlLevel,
    projectId: urlProjectId,
    taskId: urlTaskId,
    view: urlView,
  } = router.query;

  const {
    mode,
    level,
    projectId,
    taskId,
    view,
    primaryView,
    navOpen,
    contextOpen,
    hydrated,
    openProject,
    openTask,
    setView,
    setPrimaryView,
    toggleNav,
    toggleContext,
    openNav,
    closeNav,
    openContext,
    closeContext,
    setNavOpen,
    setContextOpen,
  } = useWorkroomStore();

  const isKanban = view === "kanban";

  const [projects, setProjects] = useState<Project[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingProjects, setLoadingProjects] = useState(false);
  const [loadingTasks, setLoadingTasks] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const initializedRef = useRef(false);
  const syncingRef = useRef(false);
  const syncTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // One-time URL -> Store init (after hydration)
  useEffect(() => {
    if (
      typeof window === "undefined" ||
      !router.isReady ||
      !hydrated ||
      initializedRef.current ||
      syncingRef.current
    ) {
      return;
    }

    const pId = typeof urlProjectId === "string" ? urlProjectId : undefined;
    const tId = typeof urlTaskId === "string" ? urlTaskId : undefined;
    const pv =
      typeof urlView === "string" && ["workroom", "kanban"].includes(urlView)
        ? (urlView as PrimaryView)
        : undefined;
    const v =
      typeof urlView === "string" &&
      ["doc", "chats", "activity"].includes(urlView)
        ? (urlView as View)
        : undefined;

    // Update store based on URL (one-time only)
    if (pv) {
      setPrimaryView(pv);
    }
    if (tId && pId) {
      openTask(pId, tId);
      if (v) {
        setView(v);
      }
    } else if (pId) {
      openProject(pId);
    }

    initializedRef.current = true;
  }, [
    hydrated,
    router.isReady,
    urlProjectId,
    urlTaskId,
    urlView,
    openProject,
    openTask,
    setView,
  ]);

  // Sync Store -> URL (shallow, and only when different)
  useEffect(() => {
    if (
      typeof window === "undefined" ||
      !router.isReady ||
      !hydrated ||
      !initializedRef.current ||
      syncingRef.current
    ) {
      return;
    }

    // Build nextQuery from store (omit undefined/defaults)
    const nextQuery: Record<string, string> = {};
    if (level !== "global") nextQuery.level = level;
    if (projectId) nextQuery.projectId = projectId;
    if (taskId) nextQuery.taskId = taskId;
    // Use primaryView for the view param
    if (primaryView !== "workroom") {
      nextQuery.view = primaryView;
    } else if (view !== "chats") {
      nextQuery.view = view;
    }

    // Deep compare with router.query
    const currentQuery = router.query;
    const needsUpdate =
      String(currentQuery.level || "") !== String(nextQuery.level || "") ||
      String(currentQuery.projectId || "") !==
        String(nextQuery.projectId || "") ||
      String(currentQuery.taskId || "") !== String(nextQuery.taskId || "") ||
      String(currentQuery.view || "") !== String(nextQuery.view || "") ||
      (primaryView === "kanban" && currentQuery.view !== "kanban") ||
      (primaryView === "workroom" && currentQuery.view === "kanban");

    if (needsUpdate) {
      syncingRef.current = true;

      // Clear any pending sync
      if (syncTimeoutRef.current) {
        clearTimeout(syncTimeoutRef.current);
      }

      // Debounce router.replace to coalesce rapid updates
      syncTimeoutRef.current = setTimeout(() => {
        router.replace(
          {
            pathname: "/workroom",
            query: nextQuery,
          },
          undefined,
          { shallow: true }
        );
        // Reset syncing flag after microtask
        setTimeout(() => {
          syncingRef.current = false;
        }, 0);
      }, 50);
    }
  }, [
    hydrated,
    level,
    projectId,
    taskId,
    view,
    primaryView,
    router,
    router.isReady,
  ]);

  // Cleanup sync timeout on unmount
  useEffect(() => {
    return () => {
      if (syncTimeoutRef.current) {
        clearTimeout(syncTimeoutRef.current);
      }
    };
  }, []);

  // Load data
  useEffect(() => {
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (projectId && typeof projectId === "string") {
      loadProject(projectId);
      loadTasks(projectId);
    } else {
      setSelectedProject(null);
      setTasks([]);
    }
  }, [projectId]);

  useEffect(() => {
    if (taskId && typeof taskId === "string") {
      loadTask(taskId);
    } else {
      setSelectedTask(null);
    }
  }, [taskId]);

  const loadData = async () => {
    if (typeof window === "undefined") return;

    try {
      setError(null);
      setLoadingProjects(true);
      const response = await workroomApi.getProjects();
      if (response && response.ok) {
        setProjects(response.projects || []);
        if (
          response.projects &&
          response.projects.length > 0 &&
          !projectId &&
          !taskId
        ) {
          // Auto-select first project if none selected
          const firstProject = response.projects[0];
          openProject(firstProject.id);
        } else if (response.projects && response.projects.length === 0) {
          // Auto-seed if no projects
          try {
            const seedResponse = await fetch(buildApiUrl("/dev/workroom/seed"), {
              method: "POST",
              credentials: "include",
            });
            if (seedResponse.ok) {
              const reloadResponse = await workroomApi.getProjects();
              if (
                reloadResponse.ok &&
                reloadResponse.projects &&
                reloadResponse.projects.length > 0
              ) {
                setProjects(reloadResponse.projects);
                const firstProject = reloadResponse.projects[0];
                openProject(firstProject.id);
              }
            }
          } catch (seedErr: any) {
            console.error("Failed to seed workroom:", seedErr);
            setError(`Failed to seed: ${seedErr.message}`);
          }
        }
      }
    } catch (err: any) {
      console.error("Failed to load projects:", err);
      setError(err.message || "Failed to load projects");
    } finally {
      setLoading(false);
      setLoadingProjects(false);
    }
  };

  const loadProject = async (projectId: string) => {
    try {
      const response = await workroomApi.getProject(projectId);
      if (response.ok) {
        setSelectedProject(response.project);
      }
    } catch (err) {
      console.error("Failed to load project:", err);
    }
  };

  const loadTasks = async (projectId: string) => {
    try {
      setLoadingTasks(true);
      const response = await workroomApi.getTasks(projectId);
      if (response.ok) {
        setTasks(response.tasks || []);
      }
    } catch (err) {
      console.error("Failed to load tasks:", err);
    } finally {
      setLoadingTasks(false);
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

  const handleStatusChange = async (taskId: string, status: string) => {
    try {
      await workroomApi.updateTaskStatus(taskId, status);
      await loadTasks(projectId || "");
      if (selectedTask?.id === taskId) {
        await loadTask(taskId);
      }
    } catch (err) {
      console.error("Failed to update task status:", err);
    }
  };

  const handleBreadcrumbClick = (targetLevel: Level) => {
    if (targetLevel === "global") {
      openProject(undefined);
    } else if (targetLevel === "project" && projectId) {
      openProject(projectId);
    }
  };

  const handleAttachSource = () => {
    openContext();
    // TODO: Focus Search tab in ContextPane
  };

  // Keyboard shortcuts: ⌘\ → Toggle Navigator, ⌘] → Toggle Context
  useEffect(() => {
    if (typeof window === "undefined") return;

    const isInputFocused =
      document.activeElement?.tagName === "INPUT" ||
      document.activeElement?.tagName === "TEXTAREA" ||
      (document.activeElement as HTMLElement)?.contentEditable === "true";

    const onKey = (e: KeyboardEvent) => {
      const modKey = e.metaKey || e.ctrlKey;
      if (!modKey || isInputFocused) return;

      // ⌘\ → Toggle Navigator
      if (e.key === "\\") {
        e.preventDefault();
        toggleNav();
        return;
      }

      // ⌘] → Toggle Context
      if (e.key === "]") {
        e.preventDefault();
        toggleContext();
        return;
      }
    };

    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [toggleNav, toggleContext]);

  // Legacy hotkeys
  useEffect(() => {
    if (typeof window === "undefined") return;

    const handleKeyDown = (e: KeyboardEvent) => {
      const isMac = navigator.platform.toUpperCase().indexOf("MAC") >= 0;
      const modKey = isMac ? e.metaKey : e.ctrlKey;
      const isInputFocused =
        document.activeElement?.tagName === "INPUT" ||
        document.activeElement?.tagName === "TEXTAREA" ||
        (document.activeElement as HTMLElement)?.contentEditable === "true";

      // Alt/Option+N: Toggle Navigator
      if (e.altKey && e.key === "n") {
        e.preventDefault();
        toggleNav();
        return;
      }

      // Alt/Option+C: Toggle Context
      if (e.altKey && e.key === "c") {
        e.preventDefault();
        toggleContext();
        return;
      }

      // Cmd/Ctrl+\: Toggle Navigator (legacy)
      if (modKey && e.key === "\\") {
        e.preventDefault();
        toggleNav();
        return;
      }

      // Cmd/Ctrl+.: Toggle Context (legacy)
      if (modKey && e.key === ".") {
        e.preventDefault();
        toggleContext();
        return;
      }

      // Cmd/Ctrl+K: Command palette
      if (modKey && e.key === "k") {
        e.preventDefault();
        // TODO: Open command palette
        return;
      }

      // g chords (only when not in input)
      if (!isInputFocused && modKey && e.key === "g") {
        const handleNextKey = (e2: KeyboardEvent) => {
          if (e2.key === "d" && taskId) {
            e2.preventDefault();
            setView("doc");
          } else if (e2.key === "c" && taskId) {
            e2.preventDefault();
            setView("chats");
          } else if (e2.key === "a" && taskId) {
            e2.preventDefault();
            setView("activity");
          } else if (e2.key === "k") {
            e2.preventDefault();
            setPrimaryView("kanban");
          }
          window.removeEventListener("keydown", handleNextKey);
        };
        window.addEventListener("keydown", handleNextKey);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [
    navOpen,
    contextOpen,
    taskId,
    toggleNav,
    toggleContext,
    setView,
    setPrimaryView,
  ]);

  // Responsive Navigator: default open on ≥1280px
  useEffect(() => {
    if (typeof window === "undefined") return;

    const checkWidth = () => {
      if (window.innerWidth >= 1280 && !navOpen) {
        openNav();
      } else if (window.innerWidth < 1280 && navOpen) {
        // Don't auto-close on small screens, let user control
      }
    };

    checkWidth();
    window.addEventListener("resize", checkWidth);
    return () => window.removeEventListener("resize", checkWidth);
  }, [navOpen, openNav]);

  // Auto-hide context when primaryView is kanban
  useEffect(() => {
    if (primaryView === "kanban" && contextOpen) {
      closeContext();
    }
  }, [primaryView, contextOpen, closeContext]);

  if (!hydrated) {
    return null;
  }

  if (loading) {
    return (
      <Layout>
        <div className="p-4">Loading workroom...</div>
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout>
        <div className="p-4">
          <Text variant="body" className="text-red-600 mb-2">
            Error: {error}
          </Text>
          <Button
            onClick={() => {
              setError(null);
              loadData();
            }}
          >
            Retry
          </Button>
        </div>
      </Layout>
    );
  }

  // Calculate grid template columns with named areas and persistent gutters
  const gridTemplate =
    navOpen && contextOpen && level === "task"
      ? "[nav] 260px [gut] 16px [main] 1fr [gut2] 16px [ctx] 260px"
      : navOpen && !(contextOpen && level === "task")
      ? "[nav] 260px [gut] 16px [main] 1fr [gut2] 0px [ctx] 0px"
      : !navOpen && contextOpen && level === "task"
      ? "[nav] 0px [gut] 0px [main] 1fr [gut2] 16px [ctx] 260px"
      : "[nav] 0px [gut] 0px [main] 1fr [gut2] 0px [ctx] 0px";

  return (
    <Layout variant="tight">
      <div className="max-w-[1400px] mx-auto px-4 md:px-6 pt-4 flex flex-col flex-1 min-h-0">
        <div className="flex-1 min-h-0 flex flex-col">
          {isKanban ? (
            <>
              <div className="flex-1 min-h-0 kanban-container pb-4">
                <KanbanBoard
                  tasks={tasks}
                  onUpdateTaskStatus={handleStatusChange}
                  loading={loadingTasks}
                />
              </div>
            </>
          ) : (
            <div
              className="relative flex-1 min-h-0 overflow-hidden workroom-grid pb-4"
              style={{
                display: "grid",
                gridTemplateColumns: gridTemplate,
                gridTemplateRows: "minmax(0, 1fr)",
                gap: 0,
              }}
            >
              {/* Left: Navigator */}
              {navOpen ? (
                <div
                  className="pane relative min-h-0 overflow-hidden"
                  style={{ gridArea: "nav" }}
                  aria-expanded={navOpen}
                  aria-label="Navigator"
                  id="navigator"
                >
                  <div className="scroll-area">
                    <Navigator
                      open={navOpen}
                      onClose={() => closeNav()}
                      projects={projects}
                      tasks={tasks}
                      selectedProjectId={projectId}
                      selectedTaskId={taskId}
                      loadingProjects={loadingProjects}
                      loadingTasks={loadingTasks}
                    />
                  </div>
                  <EdgeToggle
                    side="left"
                    label="Hide navigator"
                    onToggle={() => closeNav()}
                    visible={true}
                  />
                </div>
              ) : null}

              {/* Gutter 1 */}
              {navOpen && <div style={{ gridArea: "gut" }} />}

              {/* Center: Workspace */}
              <div
                className="pane relative min-h-0 overflow-hidden bg-white"
                style={{ gridArea: "main", minWidth: "640px" }}
              >
                <div className="scroll-area flex flex-col">
                  {taskId ? (
                    <Workspace
                      taskId={taskId}
                      projectId={projectId || ""}
                      projectTitle={selectedProject?.title}
                    />
                  ) : (
                    <div className="flex items-center justify-center h-full">
                      <div className="text-center">
                        <Text variant="muted" className="text-sm mb-2">
                          Select a task to view
                        </Text>
                        <Text
                          variant="caption"
                          className="text-xs text-slate-500"
                        >
                          Use Navigator or press ⌘K to search
                        </Text>
                      </div>
                    </div>
                  )}
                </div>
                <EdgeToggle
                  side="right"
                  label="Show navigator"
                  onToggle={() => openNav()}
                  visible={!navOpen}
                />
                <EdgeToggle
                  side="left"
                  label="Show context"
                  onToggle={() => openContext()}
                  visible={!contextOpen && level === "task"}
                />
              </div>

              {/* Gutter 2 */}
              {contextOpen && level === "task" && (
                <div style={{ gridArea: "gut2" }} />
              )}

              {/* Right: Context */}
              {contextOpen && level === "task" ? (
                <div
                  className="pane relative min-h-0 overflow-hidden"
                  style={{ gridArea: "ctx" }}
                  aria-expanded={contextOpen}
                  aria-label="Context"
                  id="context"
                >
                  <div className="scroll-area">
                    <ContextPane
                      projectId={projectId}
                      taskId={taskId}
                      projectTitle={selectedProject?.title}
                      taskTitle={selectedTask?.title}
                      open={contextOpen}
                      onToggle={toggleContext}
                    />
                  </div>
                  <EdgeToggle
                    side="right"
                    label="Hide context"
                    onToggle={() => closeContext()}
                    visible={true}
                  />
                </div>
              ) : null}
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
}

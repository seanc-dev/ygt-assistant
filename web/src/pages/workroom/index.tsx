import { useEffect, useState } from "react";
import { Heading, Panel, Stack, Text, Button } from "@ygt-assistant/ui";
import { Layout } from "../../components/Layout";
import { api } from "../../lib/api";
import { ProjectTree } from "../../components/ProjectTree";
import { WorkroomChat } from "../../components/WorkroomChat";
import { KanbanBoard } from "../../components/KanbanBoard";
import { useHotkeys } from "../../hooks/useHotkeys";
import { useRouter } from "next/router";

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

interface WorkroomTreeResponse {
  ok: boolean;
  tree: Project[];
}

export default function WorkroomPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [tree, setTree] = useState<Project[]>([]);
  const [selectedThread, setSelectedThread] = useState<Thread | null>(null);
  const [viewMode, setViewMode] = useState<"chat" | "kanban">("chat");
  const [settings, setSettings] = useState<any>(null);

  // Load settings for hotkeys
  useEffect(() => {
    api.settings().then((data) => setSettings(data)).catch(() => {});
  }, []);

  const loadTree = async () => {
    try {
      const data = await api.workroomTree();
      setTree((data as WorkroomTreeResponse).tree || []);
      setLoading(false);
    } catch (err) {
      console.error("Failed to load workroom tree:", err);
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTree();
  }, []);

  const handleThreadSelect = (thread: Thread) => {
    setSelectedThread(thread);
  };

  const handleTaskStatusChange = async (taskId: string, status: string) => {
    try {
      await api.updateTaskStatus(taskId, status);
      await loadTree(); // Reload tree to reflect changes
    } catch (err) {
      console.error("Failed to update task status:", err);
    }
  };

  // Hotkeys
  const hotkeyConfig = settings?.ui_prefs?.hotkeys || {};
  useHotkeys(
    {
      kanban_toggle: () => setViewMode((prev) => (prev === "kanban" ? "chat" : "kanban")),
      collapse: () => setSelectedThread(null),
      settings: () => router.push("/settings"),
    },
    hotkeyConfig,
    true
  );

  return (
    <Layout>
      <Stack gap="lg">
        <div className="flex flex-col gap-2">
          <Heading as="h1" variant="display">
            Workroom
          </Heading>
          <Text variant="muted">
            Chat-first workspace with Project → Task → Threads hierarchy.
          </Text>
        </div>

        <div className="flex gap-2">
          <Button
            variant={viewMode === "chat" ? "primary" : "outline"}
            onClick={() => setViewMode("chat")}
          >
            Chat
          </Button>
          <Button
            variant={viewMode === "kanban" ? "primary" : "outline"}
            onClick={() => setViewMode("kanban")}
          >
            Kanban
          </Button>
        </div>

        {loading && !tree.length ? (
          <Panel>
            <Text variant="muted">Loading workroom...</Text>
          </Panel>
        ) : viewMode === "chat" ? (
          <div className="grid grid-cols-3 gap-4">
            <div className="col-span-1" role="complementary" aria-label="Projects and tasks">
              <ProjectTree
                projects={tree}
                onSelectThread={handleThreadSelect}
                onCreateThread={async (taskId: string, title: string) => {
                  try {
                    await api.createThread({ task_id: taskId, title });
                    await loadTree();
                  } catch (err) {
                    console.error("Failed to create thread:", err);
                  }
                }}
                selectedThreadId={selectedThread?.id || null}
              />
            </div>
            <div className="col-span-2" role="main" aria-label="Thread chat">
              {selectedThread ? (
                <WorkroomChat
                  thread={selectedThread}
                  onTaskStatusChange={handleTaskStatusChange}
                />
              ) : (
                <Panel>
                  <Text variant="muted">Select a thread to start chatting</Text>
                </Panel>
              )}
            </div>
          </div>
        ) : (
          <KanbanBoard
            projects={tree}
            onUpdateTaskStatus={handleTaskStatusChange}
            onSelectTask={(taskId) => {
              // Find thread for task and select it
              for (const project of tree) {
                for (const task of project.children) {
                  if (task.id === taskId && task.children.length > 0) {
                    setSelectedThread(task.children[0]);
                    setViewMode("chat");
                    break;
                  }
                }
              }
            }}
          />
        )}
      </Stack>
    </Layout>
  );
}

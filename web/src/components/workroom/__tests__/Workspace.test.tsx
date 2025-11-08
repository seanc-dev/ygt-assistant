import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { Workspace } from "../Workspace";
import { useWorkroomStore } from "../../../hooks/useWorkroomStore";
import { workroomApi } from "../../../lib/workroomApi";

// Mock dependencies
vi.mock("next/router", () => ({
  useRouter: () => ({
    pathname: "/workroom",
    query: { projectId: "test-project", taskId: "test-task", view: "doc" },
    replace: vi.fn(),
  }),
}));

vi.mock("../../../hooks/useWorkroomStore", () => ({
  useWorkroomStore: vi.fn(() => ({
    taskViewState: {},
    setTaskViewState: vi.fn(),
  })),
}));

vi.mock("../../../lib/workroomApi", () => ({
  workroomApi: {
    getTask: vi.fn().mockResolvedValue({
      ok: true,
      task: {
        id: "test-task",
        title: "Test Task",
        status: "doing",
        chats: [],
        doc: { contentJSON: { type: "doc", content: [] } },
      },
    }),
    getChats: vi.fn().mockResolvedValue({
      ok: true,
      chats: [],
    }),
  },
}));

vi.mock("../TaskDoc", () => ({
  TaskDoc: ({ taskId }: { taskId: string }) => (
    <div data-testid="task-doc">TaskDoc for {taskId}</div>
  ),
}));

vi.mock("../ThreadView", () => ({
  ThreadView: ({ threadId }: { threadId: string }) => (
    <div data-testid="thread-view">ThreadView for {threadId}</div>
  ),
}));

vi.mock("../ChatTabs", () => ({
  ChatTabs: ({ chats }: { chats: any[] }) => (
    <div data-testid="chat-tabs">ChatTabs ({chats.length} chats)</div>
  ),
}));

vi.mock("../ContextPane", () => ({
  ContextPane: ({ taskId }: { taskId: string }) => (
    <div data-testid="context-pane">ContextPane for {taskId}</div>
  ),
}));

vi.mock("@ygt-assistant/ui/primitives/Button", () => ({
  __esModule: true,
  Button: ({ children, ...props }: any) => <button {...props}>{children}</button>,
}));

describe("Workspace Integration", () => {
  const defaultProps = {
    taskId: "test-task",
    projectId: "test-project",
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders Workspace component", async () => {
    render(<Workspace {...defaultProps} />);
    
    await waitFor(() => {
      expect(screen.getByTestId("task-doc")).toBeInTheDocument();
    });
  });

  it("loads task data on mount", async () => {
    render(<Workspace {...defaultProps} />);
    
    await waitFor(() => {
      expect(workroomApi.getTask).toHaveBeenCalledWith("test-task");
    });
  });

  it("loads chats on mount", async () => {
    render(<Workspace {...defaultProps} />);
    
    await waitFor(() => {
      expect(workroomApi.getChats).toHaveBeenCalledWith("test-task");
    });
  });
});


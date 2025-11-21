import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { WorkCanvas } from "../WorkCanvas";
import { useFocusContextStore } from "../../../state/focusContextStore";
import { useWorkroomContext } from "../../../hooks/useWorkroomContext";

vi.mock("../../hub/AssistantChat", () => ({
  AssistantChat: ({ actionId }: { actionId?: string }) => (
    <div data-testid="assistant-chat">Chat {actionId}</div>
  ),
}));

vi.mock("../../../hooks/useWorkroomContext", () => ({
  useWorkroomContext: vi.fn(() => ({
    workroomContext: null,
    loading: false,
    error: null,
  })),
}));

const mockedUseWorkroomContext = vi.mocked(useWorkroomContext);

const resetStore = () => {
  useFocusContextStore.setState({ current: undefined, stack: [] });
};

describe("WorkCanvas", () => {
  beforeEach(() => {
    resetStore();
    mockedUseWorkroomContext.mockReturnValue({
      workroomContext: {
        anchor: { type: "task", id: "task-1", title: "Task One", status: "doing" },
        neighborhood: {},
      },
      loading: false,
      error: null,
    });
  });

  describe("task anchors", () => {
    const baseContext = {
      anchor: { type: "task" as const, id: "task-1" },
      mode: "plan" as const,
    };

    it("renders planning section only in plan mode", () => {
      useFocusContextStore.setState({ current: baseContext, stack: [] });

      render(<WorkCanvas />);

      expect(screen.getByTestId("assistant-chat")).toBeInTheDocument();
      expect(screen.getByText(/Planning surface: schedule and options/)).toBeInTheDocument();
      expect(screen.queryByText(/Focus next: prioritized actions/)).not.toBeInTheDocument();
      expect(screen.queryByText(/Activity timeline: history and outcomes/)).not.toBeInTheDocument();
    });

    it("renders execution section only in execute mode", () => {
      useFocusContextStore.setState({
        current: { ...baseContext, mode: "execute" },
        stack: [],
      });

      render(<WorkCanvas />);

      expect(screen.getByTestId("assistant-chat")).toBeInTheDocument();
      expect(screen.getByText(/Focus next: prioritized actions will appear here/)).toBeInTheDocument();
      expect(screen.queryByText(/Planning surface: schedule and options/)).not.toBeInTheDocument();
      expect(screen.queryByText(/Activity timeline: history and outcomes/)).not.toBeInTheDocument();
    });

    it("renders review section only in review mode", () => {
      useFocusContextStore.setState({
        current: { ...baseContext, mode: "review" },
        stack: [],
      });

      render(<WorkCanvas />);

      expect(screen.getByTestId("assistant-chat")).toBeInTheDocument();
      expect(screen.getByText(/Activity timeline: history and outcomes/)).toBeInTheDocument();
      expect(screen.queryByText(/Planning surface: schedule and options/)).not.toBeInTheDocument();
      expect(screen.queryByText(/Focus next: prioritized actions/)).not.toBeInTheDocument();
    });
  });

  describe("portfolio anchors", () => {
    const anchor = { type: "portfolio" as const, id: "my_work" };

    it("shows board with planning emphasis in plan mode", () => {
      mockedUseWorkroomContext.mockReturnValue({
        workroomContext: {
          anchor: { type: "portfolio", id: "my_work", label: "My work" },
          neighborhood: {},
        },
        loading: false,
        error: null,
      });
      useFocusContextStore.setState({
        current: { anchor, mode: "plan" },
        stack: [],
      });

      render(<WorkCanvas />);

      expect(screen.getByText(/planning your work/i)).toBeInTheDocument();
      expect(screen.getAllByText(/Backlog/).length).toBeGreaterThan(0);
    });

    it("shows board with executing emphasis in execute mode", () => {
      mockedUseWorkroomContext.mockReturnValue({
        workroomContext: {
          anchor: { type: "portfolio", id: "my_work", label: "My work" },
          neighborhood: {},
        },
        loading: false,
        error: null,
      });
      useFocusContextStore.setState({
        current: { anchor, mode: "execute" },
        stack: [],
      });

      render(<WorkCanvas />);

      expect(screen.getByText(/executing your work/i)).toBeInTheDocument();
      expect(screen.getAllByText(/Backlog/).length).toBeGreaterThan(0);
    });

    it("shows board with reviewing emphasis in review mode", () => {
      mockedUseWorkroomContext.mockReturnValue({
        workroomContext: {
          anchor: { type: "portfolio", id: "my_work", label: "My work" },
          neighborhood: {},
        },
        loading: false,
        error: null,
      });
      useFocusContextStore.setState({
        current: { anchor, mode: "review" },
        stack: [],
      });

      render(<WorkCanvas />);

      expect(screen.getByText(/reviewing your work/i)).toBeInTheDocument();
      expect(screen.getAllByText(/Backlog/).length).toBeGreaterThan(0);
    });
  });

  describe("workroom context integration", () => {
    const baseContext = {
      anchor: { type: "task" as const, id: "task-1" },
      mode: "plan" as const,
    };

    it("shows loading indicator while fetching context", () => {
      useFocusContextStore.setState({ current: baseContext, stack: [] });
      mockedUseWorkroomContext.mockReturnValue({
        workroomContext: null,
        loading: true,
        error: null,
      });

      render(<WorkCanvas />);

      expect(screen.getByText(/Loading context/i)).toBeInTheDocument();
    });

    it("shows context unavailable while retaining chat on error", () => {
      useFocusContextStore.setState({ current: baseContext, stack: [] });
      mockedUseWorkroomContext.mockReturnValue({
        workroomContext: {
          anchor: { type: "task", id: "task-1", title: "Task One" },
          neighborhood: {},
        },
        loading: false,
        error: new Error("failed"),
      });

      render(<WorkCanvas />);

      expect(screen.getByText(/Context unavailable/i)).toBeInTheDocument();
      expect(screen.getByTestId("assistant-chat")).toBeInTheDocument();
    });

    it("uses workroom context anchor details in header", () => {
      useFocusContextStore.setState({ current: baseContext, stack: [] });
      mockedUseWorkroomContext.mockReturnValue({
        workroomContext: {
          anchor: { type: "task", id: "task-1", title: "Context Task", status: "doing", priority: "high" },
          neighborhood: {},
        },
        loading: false,
        error: null,
      });

      render(<WorkCanvas />);

      expect(screen.getByText(/Context Task/)).toBeInTheDocument();
      expect(screen.getByText(/Status: Doing/)).toBeInTheDocument();
      expect(screen.getByText(/Priority: high/i)).toBeInTheDocument();
    });
  });
});

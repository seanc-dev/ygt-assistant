import userEvent from "@testing-library/user-event";
import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { NeighborhoodRail } from "../NeighborhoodRail";
import { useFocusContextStore } from "../../../state/focusContextStore";
import { useWorkroomContext } from "../../../hooks/useWorkroomContext";

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

describe("NeighborhoodRail", () => {
  beforeEach(() => {
    resetStore();
    mockedUseWorkroomContext.mockReturnValue({
      workroomContext: {
        anchor: { type: "task", id: "task-1", title: "Task One" },
        neighborhood: {},
      },
      loading: false,
      error: null,
    });
  });

  it("shows empty message when no related items", () => {
    useFocusContextStore.setState({
      current: { anchor: { type: "task", id: "task-1" }, mode: "execute" },
      stack: [],
    });

    render(<NeighborhoodRail />);

    expect(screen.getByText(/No related items/i)).toBeInTheDocument();
    expect(screen.queryByText(/Related tasks/i)).not.toBeInTheDocument();
  });

  it("navigates to related task when clicked", async () => {
    const pushFocus = vi.fn();
    useFocusContextStore.setState({
      current: { anchor: { type: "task", id: "task-1" }, mode: "execute" },
      stack: [],
      pushFocus,
    });
    mockedUseWorkroomContext.mockReturnValue({
      workroomContext: {
        anchor: { type: "task", id: "task-1", title: "Task One" },
        neighborhood: { tasks: [{ id: "task-2", title: "Related task" }] },
      },
      loading: false,
      error: null,
    });

    render(<NeighborhoodRail />);

    expect(screen.getByText(/Related tasks/i)).toBeInTheDocument();

    await userEvent.click(screen.getByText("Related task"));

    expect(pushFocus).toHaveBeenCalledWith(
      { type: "task", id: "task-2" },
      { source: "direct" }
    );
  });

  it("shows loading state while neighborhood fetch is in flight", () => {
    useFocusContextStore.setState({
      current: { anchor: { type: "task", id: "task-1" }, mode: "execute" },
      stack: [],
    });
    mockedUseWorkroomContext.mockReturnValue({
      workroomContext: null,
      loading: true,
      error: null,
    });

    render(<NeighborhoodRail />);

    expect(screen.getByText(/Loading related items/i)).toBeInTheDocument();
  });
});

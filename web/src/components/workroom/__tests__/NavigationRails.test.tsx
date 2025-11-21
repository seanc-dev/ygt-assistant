import userEvent from "@testing-library/user-event";
import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";
import { WorkroomAnchorBar } from "../WorkroomAnchorBar";
import { FocusStackRail } from "../FocusStackRail";
import { useFocusContextStore } from "../../../state/focusContextStore";

const resetStore = () => {
  useFocusContextStore.setState({ current: undefined, stack: [] });
};

describe("Navigation rails", () => {
  beforeEach(() => {
    resetStore();
  });

  it("hides back controls when stack is empty", () => {
    useFocusContextStore.setState({
      current: { anchor: { type: "portfolio", id: "my_work" }, mode: "plan" },
      stack: [],
    });

    render(
      <div>
        <WorkroomAnchorBar />
        <FocusStackRail />
      </div>
    );

    expect(screen.queryByRole("button", { name: /^Back$/i })).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /Back to previous/i })
    ).not.toBeInTheDocument();
    expect(screen.getByText(/No previous focus/)).toBeInTheDocument();
  });

  it("shows back controls and pops focus when clicked", async () => {
    const previous = { anchor: { type: "portfolio", id: "my_work" }, mode: "plan" as const };
    const current = { anchor: { type: "task", id: "t1" }, mode: "execute" as const };

    useFocusContextStore.setState({ current, stack: [previous] });

    render(
      <div>
        <WorkroomAnchorBar />
        <FocusStackRail />
      </div>
    );

    const backButtons = screen.getAllByRole("button", { name: /Back/i });

    await userEvent.click(backButtons[0]);

    const state = useFocusContextStore.getState();
    expect(state.current?.anchor).toEqual(previous.anchor);
    expect(state.stack).toEqual([]);
  });

  it("renders origin labels for hub, board, and hides for direct", () => {
    useFocusContextStore.setState({
      current: { anchor: { type: "task", id: "t1" }, mode: "execute", origin: { source: "hub_surface" } },
      stack: [],
    });
    const { rerender } = render(<WorkroomAnchorBar />);

    expect(screen.getByText(/From: Hub/i)).toBeInTheDocument();

    useFocusContextStore.setState({
      current: {
        anchor: { type: "task", id: "t1" },
        mode: "execute",
        origin: { source: "board", surfaceKind: "my_work" },
      },
      stack: [],
    });
    rerender(<WorkroomAnchorBar />);
    expect(screen.getByText(/From: My work board/i)).toBeInTheDocument();

    useFocusContextStore.setState({
      current: { anchor: { type: "task", id: "t1" }, mode: "execute", origin: { source: "direct" } },
      stack: [],
    });
    rerender(<WorkroomAnchorBar />);
    expect(screen.queryByText(/From:/i)).not.toBeInTheDocument();
  });
});

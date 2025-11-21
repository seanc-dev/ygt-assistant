import userEvent from "@testing-library/user-event";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { ContextTabs } from "../ContextTabs";
import { ContextPanel } from "../../ContextPanel";
import { useContextEntries } from "../../../hooks/useContextEntries";
import { useFocusContextStore } from "../../../state/focusContextStore";

vi.mock("../../../hooks/useContextEntries", () => ({
  useContextEntries: vi.fn(),
}));

const mockedUseContextEntries = vi.mocked(useContextEntries);

describe("ContextTabs", () => {
  it("switches tabs between Neighborhood, Context, and Docs", async () => {
    render(
      <ContextTabs
        neighborhood={<div>Neighborhood content</div>}
        context={<div>Context content</div>}
        docs={<div>Docs content</div>}
      />
    );

    expect(screen.getByText("Neighborhood content")).toBeInTheDocument();
    expect(screen.queryByText("Context content")).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: /context/i }));
    expect(screen.getByText("Context content")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: /docs/i }));
    expect(screen.getByText("Docs content")).toBeInTheDocument();
  });
});

describe("ContextPanel", () => {
  beforeEach(() => {
    useFocusContextStore.setState({
      current: { anchor: { type: "task", id: "task-1" }, mode: "execute" },
      stack: [],
    });
  });

  it("shows loading and renders entries when available", async () => {
    mockedUseContextEntries.mockReturnValue({
      entries: [],
      loading: true,
      error: null,
      addEntry: vi.fn(),
      refresh: vi.fn(),
    });

    render(<ContextPanel />);

    expect(screen.getByText(/Loading context entries/i)).toBeInTheDocument();

    mockedUseContextEntries.mockReturnValue({
      entries: [
        { id: "n1", type: "note", content: "First note", createdAt: new Date().toISOString() },
      ],
      loading: false,
      error: null,
      addEntry: vi.fn(),
      refresh: vi.fn(),
    });

    render(<ContextPanel />);
    expect(screen.getByText(/Anchored to task-1/i)).toBeInTheDocument();
    expect(screen.getByText("First note")).toBeInTheDocument();
  });

  it("adds a note through the hook", async () => {
    const addEntry = vi.fn();

    mockedUseContextEntries.mockReturnValue({
      entries: [
        { id: "note-1", type: "note", content: "Latest note for task-1.", createdAt: new Date().toISOString() },
      ],
      loading: false,
      error: null,
      addEntry,
      refresh: vi.fn(),
    });

    render(<ContextPanel />);

    const input = screen.getByPlaceholderText(/add a note/i);
    await userEvent.type(input, "New note");
    await userEvent.click(screen.getByRole("button", { name: /add note/i }));

    expect(addEntry).toHaveBeenCalledWith("note", "New note");
  });
});

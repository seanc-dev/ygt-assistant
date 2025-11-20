import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import type { RefObject } from "react";
import { ReferenceSearchPanel } from "../ReferenceSearchPanel";

const createAnchorRef = (): RefObject<HTMLDivElement> => {
  const element = document.createElement("div");
  element.getBoundingClientRect = () =>
    ({
      left: 0,
      top: 0,
      width: 320,
      height: 40,
      bottom: 40,
      right: 320,
      x: 0,
      y: 0,
      toJSON: () => {},
    } as DOMRect);
  return { current: element };
};

describe("ReferenceSearchPanel", () => {
  const baseProps = {
    anchorRef: createAnchorRef(),
    query: "",
    onQueryChange: vi.fn(),
    projectOptions: [
      { id: "proj-1", title: "Project One" },
      { id: "proj-2", title: "Project Two" },
    ],
    projectId: null as string | null,
    onProjectChange: vi.fn(),
    results: [
      {
        id: "task-1",
        title: "Task One",
        projectId: "proj-1",
        projectTitle: "Project One",
      },
    ],
    loading: false,
    onSelect: vi.fn(),
    onClose: vi.fn(),
    activeIndex: 0,
    onActiveIndexChange: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders search input and project filter", () => {
    render(<ReferenceSearchPanel {...baseProps} />);
    expect(screen.getByPlaceholderText("Search tasks…")).toBeInTheDocument();
    expect(screen.getByRole("combobox")).toBeInTheDocument();
  });

  it("invokes callbacks on interactions", () => {
    render(<ReferenceSearchPanel {...baseProps} />);
    fireEvent.change(screen.getByPlaceholderText("Search tasks…"), {
      target: { value: "Task" },
    });
    expect(baseProps.onQueryChange).toHaveBeenCalledWith("Task");

    fireEvent.change(screen.getByRole("combobox"), {
      target: { value: "proj-2" },
    });
    expect(baseProps.onProjectChange).toHaveBeenCalledWith("proj-2");

    fireEvent.click(screen.getByText("Task One"));
    expect(baseProps.onSelect).toHaveBeenCalledWith(baseProps.results[0]);
  });

  it("supports keyboard navigation", () => {
    render(<ReferenceSearchPanel {...baseProps} />);
    const input = screen.getByPlaceholderText("Search tasks…");
    fireEvent.keyDown(input, { key: "ArrowDown" });
    expect(baseProps.onActiveIndexChange).toHaveBeenCalled();
  });
});


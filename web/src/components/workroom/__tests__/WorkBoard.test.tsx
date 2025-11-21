import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { useFocusContextStore } from "../../../state/focusContextStore";
import { WorkBoard } from "../WorkBoard";
import { workroomApi } from "../../../lib/workroomApi";

const createDataTransfer = () => {
  const data: Record<string, string> = {};
  return {
    setData: (key: string, value: string) => {
      data[key] = value;
    },
    getData: (key: string) => data[key],
  } as DataTransfer;
};

const resetStore = () => {
  useFocusContextStore.setState({ current: undefined, stack: [] });
};

describe("WorkBoard", () => {
  beforeEach(() => {
    resetStore();
    vi.clearAllMocks();
    vi.spyOn(workroomApi, "updateTaskStatus").mockResolvedValue({ ok: true });
  });

  it("updates task status and calls API when dropped into a new column", async () => {
    render(
      <WorkBoard boardType="portfolio" anchor={{ type: "portfolio", id: "my_work" }} />
    );

    const taskCard = screen.getByText("Sync with design").closest("div");
    const doingColumnHeader = screen.getByText("Doing");
    const columnElement = doingColumnHeader.parentElement;

    expect(taskCard).toBeTruthy();
    expect(columnElement).toBeTruthy();

    const dataTransfer = {
      getData: () => "task-3",
      setData: vi.fn(),
    } as unknown as DataTransfer;

    fireEvent.drop(columnElement as Element, { dataTransfer });

    await waitFor(() => {
      expect((workroomApi.updateTaskStatus as any)).toHaveBeenCalledWith(
        "task-3",
        "doing"
      );
    });

    const doingColumn = columnElement as HTMLElement;
    expect(doingColumn.textContent).toContain("Sync with design");
  });
});

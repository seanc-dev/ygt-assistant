import { describe, it, expect, vi, beforeEach, afterEach, beforeAll, afterAll } from "vitest";
import { render, screen, fireEvent, within } from "@testing-library/react";
import type { InteractiveSurface } from "../../../lib/llm/surfaces";
import { DayOverview } from "../DayOverview";
import { PrioritiesPanel } from "../PrioritiesPanel";
import { MyWorkSnapshot } from "../MyWorkSnapshot";
import { InboxDigest } from "../InboxDigest";
import { filterSurfacesForMode } from "../AssistantChat";
import { getMockTasks } from "../../../data/mockWorkroomData";
import { useFocusContextStore } from "../../../state/focusContextStore";
import { toggleTaskPin } from "../../../lib/hubSelectors";
import * as AssistantChatModule from "../AssistantChat";
import * as nextRouter from "next/router";
import * as focusStore from "../../../state/focusContextStore";

let assistantProps: any = null;
const pushMock = vi.fn();
let assistantSpy: ReturnType<typeof vi.spyOn> | null = null;
let routerSpy: ReturnType<typeof vi.spyOn> | null = null;
let focusSpy: ReturnType<typeof vi.spyOn> | null = null;
const pushFocusMock = vi.fn();

const buildTasks = () => getMockTasks().map((task) => ({ ...task }));

beforeAll(() => {
  routerSpy = vi.spyOn(nextRouter, "useRouter").mockImplementation(() => ({
    push: pushMock,
    replace: vi.fn(),
    prefetch: vi.fn(),
    pathname: "/",
    query: {},
    asPath: "/",
    route: "/",
  }));

  assistantSpy = vi
    .spyOn(AssistantChatModule, "AssistantChat")
    .mockImplementation((props: any) => {
      assistantProps = props;
      return <div data-testid="assistant-chat" data-mode={props.mode} />;
    });

  focusSpy = vi
    .spyOn(focusStore, "useFocusContextStore")
    .mockReturnValue({ pushFocus: pushFocusMock } as unknown as ReturnType<typeof useFocusContextStore>);
});

beforeEach(() => {
  assistantProps = null;
  pushMock.mockClear();
  pushFocusMock.mockClear();
});

afterEach(() => {
  toggleTaskPin("task-1", true);
  toggleTaskPin("task-2", true);
});

afterAll(() => {
  assistantSpy?.mockRestore();
  routerSpy?.mockRestore();
  focusSpy?.mockRestore();
});

describe("Hub orientation", () => {
  it("renders DayOverview chat with hub mode and summary", () => {
    const tasks = buildTasks();
    render(<DayOverview tasks={tasks} />);

    const chat = screen.getByTestId("assistant-chat");
    expect(chat).toBeInTheDocument();
    expect(chat).toHaveAttribute("data-mode", "hub_orientation");
    expect(assistantProps?.summary).toContain("Pinned:");
    expect(assistantProps?.surfaceRenderAllowed).toBe(true);
    expect(screen.getByText(/Open Today in Workroom/)).toBeInTheDocument();
  });

  it("routes to today's focus from the Day Overview CTA", () => {
    const tasks = buildTasks();
    render(<DayOverview tasks={tasks} />);

    fireEvent.click(screen.getByTestId("open-today-cta"));

    expect(pushFocusMock).toHaveBeenCalledWith({ type: "today" }, { source: "hub" });
    expect(pushMock).toHaveBeenCalledWith("/workroom");
  });

  it("does not render surfaces outside Day Overview", () => {
    const tasks = buildTasks();

    render(
      <>
        <PrioritiesPanel tasks={tasks} />
        <MyWorkSnapshot tasks={tasks} />
        <InboxDigest />
      </>
    );

    expect(assistantProps).toBeNull();
  });

  it("toggles priority pins and emits updates", () => {
    const tasks = buildTasks();
    const onTogglePin = vi.fn();
    render(<PrioritiesPanel tasks={tasks} onTogglePin={onTogglePin} />);

    const toggleButton = screen.getAllByLabelText(/Unpin task/)[0];
    fireEvent.click(toggleButton);

    expect(onTogglePin).toHaveBeenCalled();
    const [taskId, nextState] = onTogglePin.mock.calls[0];
    expect(taskId).toBe("task-1");
    expect(nextState).toBe(false);
  });

  it("opens pinned tasks via hub focus routing", () => {
    const tasks = buildTasks();
    render(<PrioritiesPanel tasks={tasks} />);

    fireEvent.click(screen.getAllByText("Open in Workroom")[0]);

    expect(pushFocusMock).toHaveBeenCalledWith({ type: "task", id: "task-1" }, { source: "hub" });
    expect(pushMock).toHaveBeenCalledWith("/workroom");
  });

  it("groups work snapshot and navigates via pushFocus", () => {
    const tasks = buildTasks();
    const { container } = render(<MyWorkSnapshot tasks={tasks} />);

    const groupOrder = screen
      .getAllByTestId(/group-/)
      .map((el) => el.getAttribute("data-testid"));
    expect(groupOrder).toEqual([
      "group-overdue",
      "group-doing",
      "group-ready",
      "group-blocked",
    ]);

    const overdueGroup = screen.getByTestId("group-overdue");
    expect(within(overdueGroup).getByText(/Review Q2 roadmap/)).toBeInTheDocument();
    expect(container.querySelectorAll('[draggable="true"]').length).toBe(0);

    const openButtons = screen.getAllByText("Open");
    fireEvent.click(openButtons[0]);

    expect(pushFocusMock).toHaveBeenCalledWith({ type: "task", id: "task-1" }, { source: "hub" });
    expect(pushMock).toHaveBeenCalledWith("/workroom");
  });

  it("shows inbox digest groups and triage CTA triggers focus", () => {
    render(<InboxDigest />);

    const groups = screen.getByTestId("inbox-groups");
    expect(within(groups).getAllByText(/Email|Docs|Mentions|Queue/).length).toBeGreaterThan(0);

    fireEvent.click(screen.getByTestId("open-triage-cta"));
    expect(pushFocusMock).toHaveBeenCalledWith({ type: "triage" }, { source: "hub" });
    expect(pushMock).toHaveBeenCalledWith("/workroom");
  });

  it("filters hub surfaces to allowed kinds", () => {
    const surfaces = [
      {
        surface_id: "s1",
        kind: "what_next_v1",
        title: "What next",
        payload: { primary: { headline: "hi" } },
      },
      {
        surface_id: "s2",
        kind: "priority_list_v1",
        title: "Priority list",
        payload: { items: [] },
      },
      {
        surface_id: "s3",
        kind: "triage_table_v1",
        title: "Triage",
        payload: { groups: [] },
      },
    ] as InteractiveSurface[];

    const filtered = filterSurfacesForMode(surfaces, "hub_orientation");
    expect(filtered).toHaveLength(1);
    expect(filtered?.[0].kind).toBe("what_next_v1");
  });

  it("keeps a single hub-safe surface even when priority list arrives first", () => {
    const surfaces = [
      {
        surface_id: "s4",
        kind: "priority_list_v1",
        title: "Pins",
        payload: { items: [] },
      },
      {
        surface_id: "s5",
        kind: "what_next_v1",
        title: "Next",
        payload: { primary: { headline: "hey" } },
      },
    ] as InteractiveSurface[];

    const filtered = filterSurfacesForMode(surfaces, "hub_orientation");
    expect(filtered).toHaveLength(1);
    expect(filtered?.[0].kind).toBe("priority_list_v1");
  });
});

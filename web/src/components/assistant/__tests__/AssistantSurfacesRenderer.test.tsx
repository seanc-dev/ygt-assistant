import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { AssistantSurfacesRenderer } from "../AssistantSurfacesRenderer";
import type {
  InteractiveSurface,
  SurfaceNavigateTo,
} from "../../../lib/llm/surfaces";

const whatNextSurface: InteractiveSurface = {
  surface_id: "s-what-next",
  kind: "what_next_v1",
  title: "What's Next",
  payload: {
    primary: {
      headline: "Finish pitch deck",
      body: "Needs final polish before tomorrow",
      primaryAction: {
        label: "Open task",
        navigateTo: { destination: "workroom_task", taskId: "task-123" },
      },
      secondaryActions: [
        {
          label: "Mark done",
          opToken: '[op v:1 type:"update_task_status" task_id:"task-123" status:"done"]',
        },
      ],
    },
    secondaryNotes: [{ text: "Due today" }],
  },
};

const scheduleSurface: InteractiveSurface = {
  surface_id: "s-schedule",
  kind: "today_schedule_v1",
  title: "Today",
  payload: {
    blocks: [
      {
        blockId: "b-1",
        type: "event",
        eventId: "event-1",
        label: "Investor call",
        start: "2025-11-20T15:00:00Z",
        end: "2025-11-20T15:30:00Z",
        isLocked: true,
      },
      {
        blockId: "b-2",
        type: "focus",
        taskId: "task-123",
        label: "Deck polish",
        start: "2025-11-20T16:00:00Z",
        end: "2025-11-20T16:45:00Z",
        isLocked: false,
      },
    ],
    suggestions: [
      {
        suggestionId: "sg-1",
        previewChange: "Move deck polish to 5pm",
        acceptOp: '[op v:1 type:"update_schedule" block_id:"b-2"]',
      },
    ],
    controls: {
      suggestAlternativesOp: '[op v:1 type:"schedule_suggest" blocks:"today"]',
    },
  },
};

const prioritySurface: InteractiveSurface = {
  surface_id: "s-priority",
  kind: "priority_list_v1",
  title: "Priorities",
  payload: {
    items: [
      {
        rank: 1,
        taskId: "task-123",
        label: "Finish pitch deck",
        reason: "Exec review tomorrow",
        quickActions: [
          {
            label: "Mark doing",
            opToken:
              '[op v:1 type:"update_task_status" task_id:"task-123" status:"doing"]',
          },
        ],
        navigateTo: { destination: "workroom_task", taskId: "task-123" },
      },
    ],
  },
};

const triageSurface: InteractiveSurface = {
  surface_id: "s-triage",
  kind: "triage_table_v1",
  title: "Inbox triage",
  payload: {
    groups: [
      {
        groupId: "g-1",
        label: "Newsletters",
        summary: "2 items",
        groupActions: {
          approveAllOp: '[op v:1 type:"triage_group_approve" group_id:"g-1"]',
        },
        items: [
          {
            queueItemId: "qi-1",
            source: "email",
            subject: "Weekly update",
            from: "Mia",
            approveOp: '[op v:1 type:"triage_approve" queue_id:"qi-1"]',
            declineOp: '[op v:1 type:"triage_decline" queue_id:"qi-1"]',
          },
        ],
      },
    ],
  },
};

describe("AssistantSurfacesRenderer", () => {
  it("renders nothing when there are no surfaces", () => {
    const { container } = render(<AssistantSurfacesRenderer surfaces={[]} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("renders supported surface kinds", () => {
    render(
      <AssistantSurfacesRenderer
        surfaces={[whatNextSurface, scheduleSurface, prioritySurface, triageSurface]}
      />
    );

    expect(screen.getByText("What's Next")).toBeInTheDocument();
    expect(screen.getByText("Today")).toBeInTheDocument();
    expect(screen.getByText("Priorities")).toBeInTheDocument();
    expect(screen.getByText("Inbox triage")).toBeInTheDocument();
  });

  it("invokes action handlers via child components", () => {
    const onInvokeOp = vi.fn();
    const onNavigate = vi.fn<(nav: SurfaceNavigateTo) => void>();

    render(
      <AssistantSurfacesRenderer
        surfaces={[whatNextSurface]}
        onInvokeOp={onInvokeOp}
        onNavigate={onNavigate}
      />
    );

    fireEvent.click(screen.getByRole("button", { name: "Mark done" }));
    fireEvent.click(screen.getByRole("button", { name: "Open task" }));

    expect(onInvokeOp).toHaveBeenCalledWith(
      '[op v:1 type:"update_task_status" task_id:"task-123" status:"done"]',
      { confirm: undefined }
    );
    expect(onNavigate).toHaveBeenCalledWith({
      destination: "workroom_task",
      taskId: "task-123",
    });
  });

  it("matches snapshot", () => {
    const { container } = render(
      <AssistantSurfacesRenderer surfaces={[whatNextSurface, prioritySurface]} />
    );
    expect(container).toMatchSnapshot();
  });
});


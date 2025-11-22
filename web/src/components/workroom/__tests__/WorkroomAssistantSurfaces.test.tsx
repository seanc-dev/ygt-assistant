import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { AssistantChat } from "../../hub/AssistantChat";
import type { WorkroomContext } from "../../../lib/workroomContext";

vi.mock("../../../lib/api", () => {
  const handlers: Record<string, any> = {};
  (globalThis as any).__apiHandlers = handlers;
  const api = new Proxy(
    {},
    {
      get: (_target, prop: string) => {
        if (!handlers[prop]) {
          handlers[prop] = vi.fn(async () => ({ ok: true }));
        }
        return handlers[prop];
      },
    }
  );
  return { api };
});

vi.mock("../../../lib/workroomApi", () => ({
  workroomApi: new Proxy(
    {},
    {
      get: (_target, _prop: string) => vi.fn(async () => ({ ok: true })),
    }
  ),
}));

type MockUseChatThreadResponse = {
  messages: any[];
  setMessages: any;
  threadData: any;
  mutateThreadRaw: any;
  isLoadingThread: boolean;
};

let lastMessageViews: any[] = [];

const normalizeSurfaces = (surfaces?: any[]) =>
  Array.isArray(surfaces) ? surfaces : [];

const mockChatThreadResponse = (
  surfaces?: any[],
  overrides: Partial<MockUseChatThreadResponse> = {}
): MockUseChatThreadResponse => ({
  messages: [
    {
      id: "assistant-1",
      role: "assistant",
      content: "Response",
      ts: "2024-01-01T00:00:00Z",
      surfaces: normalizeSurfaces(surfaces),
    },
  ],
  setMessages: vi.fn(),
  threadData: null,
  mutateThreadRaw: vi.fn(),
  isLoadingThread: false,
  ...overrides,
});

const useChatThreadMock = vi.fn(mockChatThreadResponse);

const workroomContext: WorkroomContext = {
  anchor: { type: "task", id: "task-123", title: "Task 123" },
  neighborhood: {
    tasks: [
      { id: "task-123", title: "Task 123" },
      { id: "task-allowed", title: "Allowed Task" },
    ],
    events: [{ id: "event-allowed", title: "Allowed Event" }],
  },
};

vi.mock("../../hub/assistantChat/useChatThread", () => ({
  useChatThread: (...args: any[]) => useChatThreadMock(...args),
}));

vi.mock("../../hub/assistantChat/MessageList", () => ({
  MessageList: ({
    messageViews,
    onInvokeSurfaceOp,
    onNavigateSurface,
  }: any) => {
    lastMessageViews = messageViews;
    return (
      <div>
        {messageViews.map((view: any) => (
          <div key={view.id} data-testid={`message-${view.id}`}>
            <span
              data-testid={`surfaces-${view.id}`}
              data-count={view.surfaces?.length ?? 0}
            >
              {view.surfaces && view.surfaces.length > 0
                ? "has-surfaces"
                : "no-surfaces"}
            </span>
            {onNavigateSurface && (
              <button
                data-testid="navigate-surface"
                onClick={() =>
                  onNavigateSurface({
                    destination: "workroom_task",
                    taskId: "nav-from-surface",
                  })
                }
              >
                Navigate
              </button>
            )}
            {onInvokeSurfaceOp && (
              <button
                data-testid="invoke-surface-op"
                onClick={() =>
                  onInvokeSurfaceOp("[op type:complete task:123]", { confirm: false })
                }
              >
                Invoke
              </button>
            )}
          </div>
        ))}
      </div>
    );
  },
}));

vi.mock("../../workroom/ActionEmbed", () => ({
  ActionEmbedComponent: () => null,
}));

vi.mock("../../shared/ActionSummary", () => ({
  ActionSummary: () => <div data-testid="action-summary" />,
}));

vi.mock("../../ui/SlashMenu", () => ({
  SlashMenu: () => null,
}));

vi.mock("../../hub/assistantChat/TokenOverlay", () => ({
  TokenOverlay: () => null,
}));

vi.mock("../../hub/assistantChat/ReferenceSearchPanel", () => ({
  ReferenceSearchPanel: () => null,
}));

vi.mock("../../hub/assistantChat/CreateTaskOpModal", () => ({
  CreateTaskOpModal: () => null,
}));

describe("AssistantChat surfaces in workroom", () => {
  beforeEach(() => {
    useChatThreadMock.mockReset();
    useChatThreadMock.mockImplementation(() => mockChatThreadResponse([]));
    const apiHandlers = (globalThis as any).__apiHandlers as
      | Record<string, any>
      | undefined;
    if (apiHandlers) {
      Object.values(apiHandlers).forEach((handler) => handler?.mockClear?.());
    }
  });

  it("suppresses surfaces when rendering is disabled", () => {
    useChatThreadMock.mockReturnValueOnce(
      mockChatThreadResponse([
        {
          surface_id: "s1",
          kind: "what_next_v1",
          title: "Next",
          payload: { primary: { headline: "Do this" } },
        },
      ])
    );

    render(
      <AssistantChat
        actionId="task:123"
        taskId="task-123"
        mode="workroom"
        surfaceRenderAllowed={false}
      />
    );

    expect(screen.getByTestId("surfaces-assistant-1").textContent).toBe(
      "no-surfaces"
    );
  });

  it("renders surfaces when allowed", () => {
    useChatThreadMock.mockImplementation(() =>
      mockChatThreadResponse([
        {
          surface_id: "s1",
          kind: "what_next_v1",
          title: "Next",
          payload: { primary: { headline: "Do this" } },
        },
      ])
    );

    render(
      <AssistantChat
        actionId="task:123"
        taskId="task-123"
        mode="workroom"
        surfaceRenderAllowed
      />
    );

    expect(screen.getByTestId("surfaces-assistant-1").textContent).toBe(
      "has-surfaces"
    );
  });

  it("caps surfaces rendered in workroom mode", () => {
    useChatThreadMock.mockImplementation(() =>
      mockChatThreadResponse([
        { surface_id: "s1", kind: "what_next_v1", title: "Next", payload: { primary: { headline: "Do this" } } },
        { surface_id: "s2", kind: "priority_list_v1", title: "Priorities", payload: { items: [{ rank: 1, taskId: "t1", label: "Task" }] } },
        { surface_id: "s3", kind: "triage_table_v1", title: "Inbox", payload: { groups: [{ groupId: "g", label: "g", items: [{ queueItemId: "q", source: "email", subject: "Subj", approveOp: "[op v:1 type:approve]", declineOp: "[op v:1 type:decline]" }] }] } },
      ])
    );

    render(
      <AssistantChat
        actionId="task:123"
        taskId="task-123"
        mode="workroom"
        surfaceRenderAllowed
      />
    );

    expect(screen.getByTestId("surfaces-assistant-1").dataset.count).toBe("2");
  });

  it("invokes operation pipeline from surfaces", async () => {
    useChatThreadMock.mockReturnValueOnce(
      mockChatThreadResponse([
        {
          surface_id: "s1",
          kind: "what_next_v1",
          title: "Next",
          payload: { primary: { headline: "Do this" } },
        },
      ])
    );

    render(
      <AssistantChat
        actionId="task:123"
        taskId="task-123"
        mode="workroom"
        surfaceRenderAllowed
      />
    );

    screen.getByTestId("invoke-surface-op").click();

    const apiHandlers = (globalThis as any).__apiHandlers as Record<string, any>;
    const approve = apiHandlers?.["assistantApproveForTask"];
    expect(approve).toBeDefined();
    expect(approve).toHaveBeenCalled();
    const approveCall = approve.mock.calls[0];
    expect(approveCall[0]).toBe("task-123");
    expect(approveCall[1]).toMatchObject({
      operation: { op: "complete", params: { task: "123" } },
    });
  });

  it("keeps surfaces scoped per chat context", () => {
    useChatThreadMock.mockImplementationOnce(() =>
      mockChatThreadResponse([
        {
          surface_id: "sa",
          kind: "what_next_v1",
          title: "A",
          payload: { primary: { headline: "A" } },
        },
      ])
    );

    const { unmount } = render(
      <AssistantChat
        actionId="task:a"
        taskId="task-a"
        threadId="thread-a"
        mode="workroom"
        surfaceRenderAllowed
      />
    );

    const firstCall = useChatThreadMock.mock.results[0]?.value as MockUseChatThreadResponse;
    expect(firstCall?.messages?.[0]?.surfaces?.length).toBe(1);

    unmount();

    useChatThreadMock.mockImplementationOnce(() => mockChatThreadResponse([]));

    render(
      <AssistantChat
        actionId="task:b"
        taskId="task-b"
        threadId="thread-b"
        mode="workroom"
        surfaceRenderAllowed
      />
    );

    expect(screen.getByTestId("surfaces-assistant-1").textContent).toBe(
      "no-surfaces"
    );
  });

  it("keeps navigation surfaces that target visible workroom tasks", () => {
    useChatThreadMock.mockImplementation(() =>
      mockChatThreadResponse([
        {
          surface_id: "s-nav-allowed",
          kind: "what_next_v1",
          title: "Next",
          payload: {
            primary: {
              headline: "Do allowed task",
              primaryAction: {
                label: "Go",
                navigateTo: { destination: "workroom_task", taskId: "task-allowed" },
              },
            },
          },
        },
      ])
    );
  
    render(
      <AssistantChat
        actionId="task:123"
        taskId="task-123"
        mode="workroom"
        surfaceRenderAllowed
        workroomContext={workroomContext}
      />
    );

    expect(screen.getByTestId("surfaces-assistant-1").textContent).toBe(
      "has-surfaces"
    );
  });

  it("filters navigation surfaces targeting hidden workroom tasks", () => {
    useChatThreadMock.mockReturnValueOnce(
      mockChatThreadResponse([
        {
          surface_id: "s-nav-hidden",
          kind: "what_next_v1",
          title: "Next",
          payload: {
            primary: {
              headline: "Do hidden task",
              primaryAction: {
                label: "Skip",
                navigateTo: { destination: "workroom_task", taskId: "task-hidden" },
              },
            },
          },
        },
      ])
    );

    render(
      <AssistantChat
        actionId="task:123"
        taskId="task-123"
        mode="workroom"
        surfaceRenderAllowed
        workroomContext={workroomContext}
      />
    );

    expect(screen.getByTestId("surfaces-assistant-1").textContent).toBe(
      "no-surfaces"
    );
  });
});

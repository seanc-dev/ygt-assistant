import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import type { ThreadResponse } from "../types";
import { useChatThread } from "../useChatThread";

vi.mock("swr", async () => {
  const actual = await vi.importActual<typeof import("swr")>("swr");
  return {
    __esModule: true,
    default: vi.fn(actual.default),
  };
});

vi.mock("../../../lib/llm/surfaces", () => ({
  parseInteractiveSurfaces: vi.fn(() => [
    { envelope_id: "env-1", surface: { kind: "what_next_v1", payload: {} } },
  ]),
}));

import useSWR from "swr";
const mockUseSWR = vi.mocked(useSWR);

describe("useChatThread", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns empty state when threadId is null", () => {
    const { result } = renderHook(() => useChatThread({ threadId: null }));
    expect(result.current.messages).toEqual([]);
    expect(result.current.isLoadingThread).toBe(false);
  });

  it("merges backend messages into state", async () => {
    const threadResponse: ThreadResponse = {
      ok: true,
      thread: {
        id: "thread-1",
        messages: [
          {
            id: "m1",
            role: "assistant",
            content: "Hello",
            ts: new Date().toISOString(),
            embeds: [],
          },
        ] as any,
      },
    };
    mockUseSWR.mockReturnValue({
      data: threadResponse,
      mutate: vi.fn(),
      isLoading: false,
    } as any);

    const { result } = renderHook(() =>
      useChatThread({ threadId: "thread-1", fetchThread: async () => threadResponse })
    );

    await waitFor(() => {
      expect(result.current.messages.length).toBe(1);
    });
    expect(result.current.messages[0].content).toBe("Hello");
  });
});


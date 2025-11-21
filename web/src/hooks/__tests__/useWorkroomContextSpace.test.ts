import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useWorkroomContextSpace } from "../useWorkroomContextSpace";
import { useFocusContextStore } from "../../state/focusContextStore";

const baseStoreState = useFocusContextStore.getState();

const resetStore = () => {
  useFocusContextStore.setState({
    current: undefined,
    stack: [],
    setFocusContext: baseStoreState.setFocusContext,
    updateFocusMode: baseStoreState.updateFocusMode,
    pushFocus: baseStoreState.pushFocus,
    popFocus: baseStoreState.popFocus,
  });
};

describe("useWorkroomContextSpace", () => {
  beforeEach(() => {
    resetStore();
    vi.restoreAllMocks();
  });

  it("fetches context space for the active focus anchor", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ contextSpace: { foo: "bar" } }),
      } as Response);

    useFocusContextStore.setState({ current: { anchor: { type: "task", id: "t-1" }, mode: "plan" }, stack: [] });

    const { result } = renderHook(() => useWorkroomContextSpace());

    expect(result.current.loading).toBe(true);

    await waitFor(() => expect(result.current.contextSpace).toEqual({ foo: "bar" }));
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/workroom/context/space?anchorType=task&anchorId=t-1",
      expect.objectContaining({ signal: expect.any(AbortSignal) })
    );
  });

  it("sets error state when the fetch fails", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: "Server error",
      json: () => Promise.resolve({ error: "boom" }),
    } as Response);

    useFocusContextStore.setState({ current: { anchor: { type: "task", id: "t-2" }, mode: "plan" }, stack: [] });

    const { result } = renderHook(() => useWorkroomContextSpace());

    await waitFor(() => expect(result.current.error).toBeInstanceOf(Error));
    expect(result.current.loading).toBe(false);
    expect(result.current.contextSpace).toBeNull();
  });

  it("merges updates returned from POST into the existing context space", async () => {
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ contextSpace: { foo: "bar", nested: { a: 1 } } }),
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ contextSpace: { nested: { b: 2 }, extra: true } }),
      } as Response);

    useFocusContextStore.setState({ current: { anchor: { type: "task", id: "t-3" }, mode: "plan" }, stack: [] });

    const { result } = renderHook(() => useWorkroomContextSpace());

    await waitFor(() => expect(result.current.contextSpace).toBeTruthy());

    await act(async () => {
      await result.current.updateContextSpace({ nested: { b: 2 } });
    });

    expect(result.current.contextSpace).toEqual({
      foo: "bar",
      nested: { b: 2 },
      extra: true,
    });
    expect(result.current.loading).toBe(false);
  });
});

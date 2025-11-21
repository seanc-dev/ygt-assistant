import { act } from "@testing-library/react";
import { describe, expect, beforeEach, it } from "vitest";
import { useFocusContextStore } from "../focusContextStore";

const resetStore = () => {
  useFocusContextStore.setState({ current: undefined, stack: [] });
};

describe("focusContextStore", () => {
  beforeEach(() => {
    resetStore();
  });

  it("starts with undefined current and empty stack", () => {
    const state = useFocusContextStore.getState();
    expect(state.current).toBeUndefined();
    expect(state.stack).toEqual([]);
  });

  it("pushFocus defaults to plan for portfolio/project and execute for task/event", () => {
    act(() => {
      useFocusContextStore.getState().pushFocus({ type: "portfolio", id: "p1" });
    });
    let state = useFocusContextStore.getState();
    expect(state.current?.mode).toBe("plan");
    expect(state.current?.anchor).toEqual({ type: "portfolio", id: "p1" });

    act(() => {
      useFocusContextStore.getState().pushFocus({ type: "task", id: "t1" });
    });
    state = useFocusContextStore.getState();
    expect(state.current?.mode).toBe("execute");
    expect(state.current?.anchor).toEqual({ type: "task", id: "t1" });
    expect(state.stack.length).toBe(1);
  });

  it("pushFocus pushes existing current onto the stack", () => {
    useFocusContextStore.setState({
      current: { anchor: { type: "project", id: "proj" }, mode: "plan" },
      stack: [],
    });

    act(() => {
      useFocusContextStore.getState().pushFocus({ type: "task", id: "t1" });
    });

    const state = useFocusContextStore.getState();
    expect(state.stack).toHaveLength(1);
    expect(state.stack[0]).toEqual({
      anchor: { type: "project", id: "proj" },
      mode: "plan",
    });
    expect(state.current?.anchor).toEqual({ type: "task", id: "t1" });
  });

  it("setFocusContext replaces without pushing when pushToStack is false", () => {
    useFocusContextStore.setState({
      current: { anchor: { type: "task", id: "t1" }, mode: "execute" },
      stack: [],
    });

    act(() => {
      useFocusContextStore.getState().setFocusContext(
        { anchor: { type: "task", id: "t2" }, mode: "execute" },
        { pushToStack: false }
      );
    });

    const state = useFocusContextStore.getState();
    expect(state.current?.anchor.id).toBe("t2");
    expect(state.stack).toEqual([]);
  });

  it("setFocusContext pushes previous current by default", () => {
    useFocusContextStore.setState({
      current: { anchor: { type: "task", id: "t1" }, mode: "execute" },
      stack: [],
    });

    act(() => {
      useFocusContextStore.getState().setFocusContext({
        anchor: { type: "task", id: "t2" },
        mode: "execute",
      });
    });

    const state = useFocusContextStore.getState();
    expect(state.stack).toHaveLength(1);
    expect(state.stack[0].anchor.id).toBe("t1");
    expect(state.current?.anchor.id).toBe("t2");
  });

  it("popFocus restores the last stack entry", () => {
    useFocusContextStore.setState({
      current: { anchor: { type: "task", id: "t2" }, mode: "execute" },
      stack: [
        { anchor: { type: "portfolio", id: "my_work" }, mode: "plan" },
      ],
    });

    act(() => {
      useFocusContextStore.getState().popFocus();
    });

    const state = useFocusContextStore.getState();
    expect(state.current?.anchor).toEqual({ type: "portfolio", id: "my_work" });
    expect(state.stack).toEqual([]);
  });

  it("popFocus does nothing when stack is empty", () => {
    useFocusContextStore.setState({
      current: { anchor: { type: "task", id: "t1" }, mode: "execute" },
      stack: [],
    });

    act(() => {
      useFocusContextStore.getState().popFocus();
    });

    const state = useFocusContextStore.getState();
    expect(state.current?.anchor.id).toBe("t1");
    expect(state.stack).toEqual([]);
  });
});

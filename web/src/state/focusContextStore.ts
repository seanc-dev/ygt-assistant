import { create } from "zustand";
import {
  type FocusAnchor,
  type FocusContext,
  type FocusMode,
  type FocusOrigin,
} from "../lib/focusContext";

type FocusContextStore = {
  current?: FocusContext;
  stack: FocusContext[];
  setFocusContext: (
    ctx: FocusContext,
    options?: { pushToStack?: boolean }
  ) => void;
  updateFocusMode: (mode: FocusMode) => void;
  pushFocus: (anchor: FocusAnchor, origin?: FocusOrigin) => void;
  popFocus: () => void;
};

const getDefaultModeForAnchor = (anchor: FocusAnchor): FocusMode => {
  if (anchor.type === "portfolio" || anchor.type === "project") {
    return "plan";
  }
  return "execute";
};

export const useFocusContextStore = create<FocusContextStore>((set) => ({
  current: undefined,
  stack: [],
  setFocusContext: (ctx, options) => {
    set((state) => {
      const shouldPush = options?.pushToStack ?? true;
      const nextStack = shouldPush && state.current
        ? [...state.stack, state.current]
        : state.stack;
      return {
        current: ctx,
        stack: nextStack,
      };
    });
  },
  updateFocusMode: (mode) => {
    set((state) => {
      if (!state.current) return state;
      return {
        ...state,
        current: {
          ...state.current,
          mode,
        },
      };
    });
  },
  pushFocus: (anchor, origin) => {
    const nextContext: FocusContext = {
      anchor,
      origin,
      mode: getDefaultModeForAnchor(anchor),
    };
    set((state) => ({
      stack: state.current ? [...state.stack, state.current] : state.stack,
      current: nextContext,
    }));
  },
  popFocus: () => {
    set((state) => {
      if (state.stack.length === 0) return state;
      const previous = state.stack[state.stack.length - 1];
      return {
        current: previous,
        stack: state.stack.slice(0, -1),
      };
    });
  },
}));

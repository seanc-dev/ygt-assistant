import { describe, it, expect } from "vitest";
import { create } from "../zustandShim";

describe("zustandShim", () => {
  it("supports direct form: create(initializer)", () => {
    interface TestState {
      count: number;
      increment: () => void;
    }

    const useStore = create<TestState>((set) => ({
      count: 0,
      increment: () => set((state) => ({ count: state.count + 1 })),
    }));

    expect(useStore.getState().count).toBe(0);
    useStore.getState().increment();
    expect(useStore.getState().count).toBe(1);
  });

  it("supports curried form: create<State>()(initializer)", () => {
    interface TestState {
      count: number;
      increment: () => void;
    }

    // This is the form used by useWorkroomStore
    const useStore = create<TestState>()((set) => ({
      count: 0,
      increment: () => set((state) => ({ count: state.count + 1 })),
    }));

    expect(useStore.getState().count).toBe(0);
    useStore.getState().increment();
    expect(useStore.getState().count).toBe(1);
  });

  it("supports curried form with middleware-like wrapper", () => {
    interface TestState {
      count: number;
      increment: () => void;
    }

    // Simulate middleware that wraps the initializer (like persist does)
    const mockPersist = <T,>(
      initializer: (set: any, get: any, api: any) => T
    ) => {
      return (set: any, get: any, api: any) => {
        const state = initializer(set, get, api);
        // Middleware can modify state or behavior
        return state;
      };
    };

    // This mimics: create<State>()(persist(initializer, config))
    // This is the exact pattern used by useWorkroomStore
    const useStore = create<TestState>()(
      mockPersist((set) => ({
        count: 0,
        increment: () => set((state) => ({ count: state.count + 1 })),
      }))
    );

    expect(useStore.getState().count).toBe(0);
    useStore.getState().increment();
    expect(useStore.getState().count).toBe(1);
  });
});


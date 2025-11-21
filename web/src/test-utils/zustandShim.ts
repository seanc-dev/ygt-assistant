import { useSyncExternalStore } from "react";

type StateCreator<T> = (
  setState: (
    partial: Partial<T> | ((state: T) => Partial<T>),
    replace?: boolean
  ) => void,
  getState: () => T,
  api: StoreApi<T>
) => T;

type StoreApi<T> = {
  setState: (
    partial: Partial<T> | ((state: T) => Partial<T>),
    replace?: boolean
  ) => void;
  getState: () => T;
  subscribe: (listener: () => void) => () => void;
};

export function create<T>(initializer: StateCreator<T>) {
  let state: T;
  const listeners = new Set<() => void>();

  const setState: StoreApi<T>["setState"] = (partial, replace) => {
    const nextState =
      typeof partial === "function" ? (partial as (s: T) => Partial<T>)(state) : partial;
    state = (replace ? nextState : { ...state, ...(nextState as Partial<T>) }) as T;
    listeners.forEach((listener) => listener());
  };

  const getState = () => state;
  const subscribe: StoreApi<T>["subscribe"] = (listener) => {
    listeners.add(listener);
    return () => listeners.delete(listener);
  };

  const api: StoreApi<T> = {
    setState,
    getState,
    subscribe,
  };

  state = initializer(setState, getState, api);

  const useStore = <U>(selector: (state: T) => U = (s) => s as unknown as U) =>
    useSyncExternalStore(
      subscribe,
      () => selector(state),
      () => selector(state)
    );

  (useStore as any).getState = getState;
  (useStore as any).setState = setState;
  (useStore as any).subscribe = subscribe;
  (useStore as any).destroy = () => {
    listeners.clear();
  };

  return useStore as any;
}

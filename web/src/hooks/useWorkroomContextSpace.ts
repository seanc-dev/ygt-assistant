import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useFocusContextStore } from "../state/focusContextStore";

export type WorkroomContextSpace = Record<string, unknown>;

const buildUrlParams = (anchorType: string, anchorId: string) => {
  const params = new URLSearchParams({ anchorType, anchorId });
  return params.toString();
};

export function useWorkroomContextSpace() {
  const { current } = useFocusContextStore();
  const anchor = current?.anchor;
  const [contextSpace, setContextSpace] = useState<WorkroomContextSpace | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const requestRef = useRef(0);
  const isMountedRef = useRef(false);

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  useEffect(() => {
    if (!anchor) {
      setContextSpace(null);
      setError(null);
      setLoading(false);
      return undefined;
    }

    const requestId = requestRef.current + 1;
    requestRef.current = requestId;
    const controller = new AbortController();

    const anchorId = anchor.id ?? (anchor.type === "portfolio" ? "my_work" : undefined);
    if (!anchorId) {
      setContextSpace(null);
      setLoading(false);
      return undefined;
    }

    setLoading(true);
    setError(null);

    const params = buildUrlParams(anchor.type, anchorId);

    fetch(`/api/workroom/context/space?${params}`, { signal: controller.signal })
      .then(async (res) => {
        if (!res.ok) {
          const message = await res
            .json()
            .catch(() => ({ error: `${res.status} ${res.statusText}` }));
          throw new Error(message.error || message.detail || `${res.status} ${res.statusText}`);
        }
        return res.json();
      })
      .then((data) => {
        if (!isMountedRef.current || requestRef.current !== requestId) return;
        setContextSpace((data as { contextSpace?: WorkroomContextSpace }).contextSpace ?? data);
      })
      .catch((err) => {
        if (err.name === "AbortError" || !isMountedRef.current) return;
        setError(err instanceof Error ? err : new Error("Failed to load context space"));
      })
      .finally(() => {
        if (requestRef.current === requestId && isMountedRef.current) {
          setLoading(false);
        }
      });

    return () => {
      controller.abort();
    };
  }, [anchor]);

  const updateContextSpace = useCallback(
    async (updates: WorkroomContextSpace) => {
      if (!anchor) return null;

      const anchorId = anchor.id ?? (anchor.type === "portfolio" ? "my_work" : undefined);
      if (!anchorId) return null;

      const requestId = requestRef.current + 1;
      requestRef.current = requestId;
      const controller = new AbortController();

      setLoading(true);
      setError(null);

      try {
        const params = buildUrlParams(anchor.type, anchorId);
        const res = await fetch(`/api/workroom/context/space?${params}`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(updates),
          signal: controller.signal,
        });
        if (!res.ok) {
          const message = await res
            .json()
            .catch(() => ({ error: `${res.status} ${res.statusText}` }));
          throw new Error(message.error || message.detail || `${res.status} ${res.statusText}`);
        }
        const data = await res.json();
        const nextContextSpace = (data as { contextSpace?: WorkroomContextSpace }).contextSpace ?? data;
        if (!isMountedRef.current || requestRef.current !== requestId) return nextContextSpace;
        setContextSpace((prev) => ({ ...(prev ?? {}), ...(nextContextSpace as object) }));
        return nextContextSpace;
      } catch (err) {
        if ((err as Error).name === "AbortError" || !isMountedRef.current) return null;
        setError(err instanceof Error ? err : new Error("Failed to update context space"));
        throw err;
      } finally {
        if (requestRef.current === requestId && isMountedRef.current) {
          setLoading(false);
        }
      }
    },
    [anchor]
  );

  const value = useMemo(
    () => ({ contextSpace, loading, error, updateContextSpace }),
    [contextSpace, loading, error, updateContextSpace]
  );

  return value;
}

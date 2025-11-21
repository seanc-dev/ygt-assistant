import { useEffect, useMemo, useRef, useState } from "react";
import type { FocusAnchor } from "../lib/focusContext";
import { useFocusContextStore } from "../state/focusContextStore";
import type { WorkroomContext } from "../lib/workroomContext";

const buildFallbackContext = (anchor: FocusAnchor): WorkroomContext => ({
  anchor:
    anchor.type === "task"
      ? { type: "task", id: anchor.id || "unknown", title: anchor.id || "Task" }
      : anchor.type === "event"
        ? { type: "event", id: anchor.id || "unknown", title: anchor.id || "Event" }
        : anchor.type === "project"
          ? { type: "project", id: anchor.id || "unknown", name: anchor.id || "Project" }
          : { type: "portfolio", id: "my_work", label: "My work" },
  neighborhood: {},
});

export function useWorkroomContext() {
  const { current } = useFocusContextStore();
  const [workroomContext, setWorkroomContext] = useState<WorkroomContext | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const requestRef = useRef(0);

  const anchor = current?.anchor;

  useEffect(() => {
    if (!anchor) {
      setWorkroomContext(null);
      setError(null);
      setLoading(false);
      return undefined;
    }

    const requestId = requestRef.current + 1;
    requestRef.current = requestId;
    const controller = new AbortController();

    const anchorId = anchor.id ?? (anchor.type === "portfolio" ? "my_work" : undefined);
    if (!anchorId) {
      setWorkroomContext(buildFallbackContext(anchor));
      setLoading(false);
      return undefined;
    }

    setLoading(true);
    setError(null);

    const params = new URLSearchParams({ anchorType: anchor.type, anchorId });

    fetch(`/api/workroom/context?${params.toString()}`, { signal: controller.signal })
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
        if (requestRef.current !== requestId) return;
        setWorkroomContext(data.workroomContext as WorkroomContext);
      })
      .catch((err) => {
        if (err.name === "AbortError") return;
        setError(err instanceof Error ? err : new Error("Failed to load context"));
        setWorkroomContext(buildFallbackContext(anchor));
      })
      .finally(() => {
        if (requestRef.current === requestId) {
          setLoading(false);
        }
      });

    return () => {
      controller.abort();
    };
  }, [anchor]);

  const value = useMemo(
    () => ({ workroomContext, loading, error }),
    [workroomContext, loading, error]
  );

  return value;
}

import { useEffect, useMemo, useRef, useState } from "react";
import { useFocusContextStore } from "../state/focusContextStore";

export type ContextEntryType = "note" | "decision" | "constraint";

export interface ContextEntry {
  id: string;
  type: ContextEntryType;
  content: string;
  createdAt: string;
  author?: string;
}

type HookState = {
  entries: ContextEntry[];
  loading: boolean;
  error: Error | null;
  addEntry: (type: ContextEntryType, content: string) => void;
  refresh: () => void;
};

const buildSeedEntries = (anchorLabel: string | undefined): ContextEntry[] => {
  const label = anchorLabel || "current focus";
  return [
    {
      id: "note-1",
      type: "note",
      content: `Latest note for ${label}.`,
      author: "You",
      createdAt: new Date().toISOString(),
    },
    {
      id: "decision-1",
      type: "decision",
      content: `Decision pending for ${label}.`,
      author: "Autopilot",
      createdAt: new Date().toISOString(),
    },
    {
      id: "constraint-1",
      type: "constraint",
      content: `Constraint to watch for ${label}.`,
      author: "System",
      createdAt: new Date().toISOString(),
    },
  ];
};

export function useContextEntries(): HookState {
  const { current } = useFocusContextStore();
  const [entries, setEntries] = useState<ContextEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const requestRef = useRef(0);

  const anchorLabel = useMemo(() => current?.anchor.id || current?.anchor.type, [
    current,
  ]);

  const hydrateEntries = () => {
    if (!current?.anchor) {
      setEntries([]);
      setLoading(false);
      setError(null);
      return;
    }

    const requestId = requestRef.current + 1;
    requestRef.current = requestId;
    setLoading(true);
    setError(null);

    const timer = setTimeout(() => {
      if (requestRef.current !== requestId) return;

      if (current.anchor.id === "error") {
        setError(new Error("Failed to load context entries."));
        setEntries([]);
        setLoading(false);
        return;
      }

      setEntries(buildSeedEntries(anchorLabel));
      setLoading(false);
    }, 120);

    return () => clearTimeout(timer);
  };

  useEffect(() => {
    const cleanup = hydrateEntries();
    return cleanup;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [anchorLabel, current?.anchor?.id, current?.anchor?.type]);

  const addEntry = (type: ContextEntryType, content: string) => {
    if (!content.trim()) return;
    setEntries((prev) => [
      {
        id: `${type}-${Date.now()}`,
        type,
        content,
        author: "You",
        createdAt: new Date().toISOString(),
      },
      ...prev,
    ]);
  };

  return {
    entries,
    loading,
    error,
    addEntry,
    refresh: () => {
      hydrateEntries();
    },
  };
}

import { useMemo, useState } from "react";
import { Text } from "@lucid-work/ui";
import { useFocusContextStore } from "../state/focusContextStore";
import {
  type ContextEntryType,
  useContextEntries,
} from "../hooks/useContextEntries";

type DraftState = Record<ContextEntryType, string>;

const defaultDrafts: DraftState = {
  note: "",
  decision: "",
  constraint: "",
};

export function ContextPanel() {
  const { current } = useFocusContextStore();
  const { entries, loading, error, addEntry, refresh } = useContextEntries();
  const [drafts, setDrafts] = useState<DraftState>(defaultDrafts);

  const anchorLabel = useMemo(() => {
    if (!current?.anchor) return "No focus selected";
    const { anchor } = current;
    return anchor.id || anchor.type;
  }, [current]);

  const handleAdd = (type: ContextEntryType) => {
    const content = drafts[type];
    addEntry(type, content);
    setDrafts((prev) => ({ ...prev, [type]: "" }));
  };

  const renderEntries = (type: ContextEntryType) => {
    const filtered = entries.filter((entry) => entry.type === type);
    if (filtered.length === 0) {
      return (
        <Text variant="caption" className="text-xs text-slate-500">
          Nothing recorded yet.
        </Text>
      );
    }

    return (
      <div className="flex flex-col gap-2" data-testid={`${type}-list`}>
        {filtered.map((entry) => (
          <div
            key={entry.id}
            className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-sm text-slate-700"
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-600">
                {entry.author || "Unknown"}
              </span>
              <span className="text-[11px] text-slate-400">
                {new Date(entry.createdAt).toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </span>
            </div>
            <div className="mt-1 text-sm text-slate-800">{entry.content}</div>
          </div>
        ))}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex flex-col gap-2 rounded-lg border border-slate-200 bg-slate-50 p-3 text-sm text-slate-600">
        <Text variant="body" className="text-sm font-semibold text-slate-700">
          Context
        </Text>
        <Text variant="caption" className="text-xs text-slate-500">
          Loading context entries...
        </Text>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col gap-3 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
        <Text variant="body" className="text-sm font-semibold">
          Context unavailable
        </Text>
        <Text variant="caption" className="text-xs">
          {error.message || "Unable to load context entries."}
        </Text>
        <button
          type="button"
          onClick={() => refresh()}
          className="self-start rounded-md bg-amber-600 px-3 py-1 text-xs font-medium text-white shadow-sm transition hover:bg-amber-700"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4 text-sm text-slate-700" data-testid="context-panel">
      <div className="flex flex-col gap-1">
        <Text variant="body" className="text-sm font-semibold text-slate-800">
          Context
        </Text>
        <Text variant="caption" className="text-xs text-slate-500">
          Anchored to {anchorLabel}
        </Text>
      </div>

      {([
        {
          type: "note" as const,
          label: "Notes",
          helper: "Quick facts and observations for the current focus.",
        },
        {
          type: "decision" as const,
          label: "Decisions",
          helper: "Record choices made or pending approvals.",
        },
        {
          type: "constraint" as const,
          label: "Constraints",
          helper: "Track limitations, blockers, or risks.",
        },
      ]).map((section) => (
        <div key={section.type} className="flex flex-col gap-2">
          <div className="flex items-center justify-between gap-2">
            <div>
              <div className="text-sm font-semibold text-slate-800">
                {section.label}
              </div>
              <div className="text-xs text-slate-500">{section.helper}</div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <input
              type="text"
              value={drafts[section.type]}
              onChange={(e) =>
                setDrafts((prev) => ({ ...prev, [section.type]: e.target.value }))
              }
              placeholder={`Add a ${section.label.toLowerCase().slice(0, -1)}...`}
              className="w-full rounded-md border border-slate-200 px-3 py-2 text-sm focus:border-slate-400 focus:outline-none"
            />
            <button
              type="button"
              disabled={!drafts[section.type].trim()}
              onClick={() => handleAdd(section.type)}
              className="rounded-md bg-slate-900 px-3 py-2 text-xs font-medium text-white shadow-sm transition disabled:cursor-not-allowed disabled:bg-slate-200"
            >
              Add {section.type}
            </button>
          </div>

          {renderEntries(section.type)}
        </div>
      ))}
    </div>
  );
}

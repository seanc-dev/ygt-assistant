import { useMemo, useState } from "react";
import type {
  ContextAddEntry,
  ContextAddV1Surface,
  SurfaceNavigateTo,
} from "../../lib/llm/surfaces";

type ContextAddSurfaceProps = {
  surface: ContextAddV1Surface;
  onUpdateContextSpace?: (entries: ContextAddEntry[]) => Promise<void> | void;
  onNavigate?: (nav: SurfaceNavigateTo) => void;
};

export function ContextAddSurface({
  surface,
  onUpdateContextSpace,
  onNavigate,
}: ContextAddSurfaceProps) {
  const { title, payload } = surface;
  const [pendingIds, setPendingIds] = useState<Set<string>>(new Set());

  const entries = useMemo(() => payload.entries ?? [], [payload.entries]);

  const handleAdd = async (entry: ContextAddEntry) => {
    if (!onUpdateContextSpace) return;
    const entryKey = entry.id || entry.title;
    setPendingIds((current) => new Set(current).add(entryKey));
    try {
      await onUpdateContextSpace([entry]);
    } finally {
      setPendingIds((current) => {
        const next = new Set(current);
        next.delete(entryKey);
        return next;
      });
    }
  };

  const handleAddAll = async () => {
    if (!onUpdateContextSpace || !entries.length) return;
    setPendingIds(new Set(entries.map((entry) => entry.id || entry.title)));
    try {
      await onUpdateContextSpace(entries);
    } finally {
      setPendingIds(new Set());
    }
  };

  return (
    <div className="rounded-2xl border border-slate-200 bg-white shadow-sm p-5 text-slate-900">
      <div className="text-xs uppercase tracking-wide text-slate-500 mb-1">
        {title}
      </div>
      <h3 className="font-semibold text-lg leading-tight">Add to context</h3>
      <p className="text-sm text-slate-600 mt-1">
        Keep the assistant aware of related work by adding these items.
      </p>

      <div className="mt-4 space-y-3">
        {entries.map((entry, idx) => {
          const entryKey = entry.id || `${entry.title}-${idx}`;
          const isPending = pendingIds.has(entryKey);
          return (
            <div
              key={entryKey}
              className="flex items-start justify-between gap-3 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5"
            >
              <div className="flex-1 min-w-0">
                <div className="text-sm font-semibold text-slate-800 truncate">
                  {entry.title}
                </div>
                {(entry.subtitle || entry.detail || entry.source) && (
                  <div className="text-xs text-slate-600 mt-0.5 space-y-0.5">
                    {entry.subtitle && <div>{entry.subtitle}</div>}
                    {entry.detail && <div className="text-slate-500">{entry.detail}</div>}
                    {entry.source && (
                      <div className="text-slate-500">Source: {entry.source}</div>
                    )}
                  </div>
                )}
              </div>
              <div className="flex flex-col items-end gap-2">
                <button
                  type="button"
                  className="px-3 py-1.5 rounded-full bg-slate-900 text-white text-xs font-medium hover:bg-slate-800 transition disabled:opacity-60 disabled:cursor-not-allowed"
                  onClick={() => handleAdd(entry)}
                  disabled={isPending}
                  data-testid={`context-add-${idx}`}
                >
                  {isPending ? "Adding..." : "Add"}
                </button>
                {entry.id && (
                  <button
                    type="button"
                    className="text-xs text-blue-700 hover:underline"
                    onClick={() =>
                      onNavigate?.({
                        destination: "workroom_task",
                        taskId: entry.id!,
                      })
                    }
                  >
                    View
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {entries.length > 1 && (
        <div className="mt-4 flex justify-end">
          <button
            type="button"
            className="px-4 py-2 rounded-full border border-slate-300 text-sm text-slate-700 hover:bg-slate-50 transition disabled:opacity-60 disabled:cursor-not-allowed"
            onClick={handleAddAll}
            disabled={pendingIds.size > 0}
            data-testid="context-add-all"
          >
            Add all
          </button>
        </div>
      )}
    </div>
  );
}


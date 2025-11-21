import { useMemo, useState } from "react";
import { useFocusContextStore } from "../state/focusContextStore";
import { useWorkroomContext } from "../hooks/useWorkroomContext";
import { formatTimeWindow, statusLabelMap } from "../data/mockWorkroomData";

type TabKey = "focus" | "notes" | "neighborhood";

export function ContextPanel() {
  const { current } = useFocusContextStore();
  const { workroomContext, loading, error } = useWorkroomContext();
  const [activeTab, setActiveTab] = useState<TabKey>("focus");
  const [notesByAnchor, setNotesByAnchor] = useState<Record<string, string>>({});

  const anchorKey = useMemo(() => {
    if (!current) return "";
    return `${current.anchor.type}:${current.anchor.id || "root"}`;
  }, [current]);

  const anchorDetail = workroomContext?.anchor;
  const noteValue = notesByAnchor[anchorKey] ?? "";

  if (!current) {
    return null;
  }

  const headerLabel = anchorDetail
    ? anchorDetail.type === "task"
      ? anchorDetail.title
      : anchorDetail.type === "project"
        ? anchorDetail.name
        : anchorDetail.type === "event"
          ? anchorDetail.title
          : anchorDetail.type === "portfolio"
            ? anchorDetail.label
            : current.anchor.id || current.anchor.type
    : current.anchor.id || current.anchor.type;

  const handleNoteChange = (value: string) => {
    setNotesByAnchor((prev) => ({ ...prev, [anchorKey]: value }));
  };

  const renderFocusSummary = () => {
    if (loading) {
      return <div className="text-xs text-slate-500">Loading context…</div>;
    }
    if (error) {
      return <div className="text-xs text-amber-700">Context unavailable.</div>;
    }

    if (!anchorDetail) {
      return (
        <div className="rounded border border-dashed border-slate-200 bg-slate-50 p-3 text-xs text-slate-600">
          No context details available for this anchor.
        </div>
      );
    }

    const statusLabel =
      anchorDetail.type === "task" && anchorDetail.status
        ? statusLabelMap[anchorDetail.status] || anchorDetail.status
        : undefined;

    const timeLabel =
      anchorDetail.type === "event"
        ? formatTimeWindow(anchorDetail.start, anchorDetail.end)
        : anchorDetail.type === "task"
          ? formatTimeWindow()
          : undefined;

    return (
      <div className="space-y-2 text-xs text-slate-700">
        <div className="flex flex-wrap items-center gap-2">
          <span className="rounded-full bg-blue-50 px-2 py-1 text-[11px] font-semibold uppercase text-blue-700">
            {anchorDetail.type}
          </span>
          {statusLabel && (
            <span className="rounded-full bg-slate-100 px-2 py-1 text-[11px] font-medium text-slate-700">
              Status: {statusLabel}
            </span>
          )}
          {anchorDetail.type === "task" && anchorDetail.priority && (
            <span className="rounded-full bg-amber-50 px-2 py-1 text-[11px] font-medium text-amber-800">
              Priority: {anchorDetail.priority}
            </span>
          )}
          {timeLabel && (
            <span className="rounded-full bg-slate-50 px-2 py-1 text-[11px] font-medium text-slate-700">
              {timeLabel}
            </span>
          )}
        </div>

        {anchorDetail.type === "event" && anchorDetail.linkedTaskIds?.length ? (
          <div className="rounded-md bg-slate-50 p-3">
            <div className="text-[11px] font-semibold text-slate-700">Linked tasks</div>
            <div className="mt-1 flex flex-wrap gap-2 text-[11px] text-slate-600">
              {anchorDetail.linkedTaskIds.map((id) => (
                <span key={id} className="rounded-full bg-white px-2 py-1 shadow-sm">
                  {id}
                </span>
              ))}
            </div>
          </div>
        ) : null}

        {anchorDetail.type === "task" && anchorDetail.linkedEventId ? (
          <div className="rounded-md bg-slate-50 p-3">
            <div className="text-[11px] font-semibold text-slate-700">Linked event</div>
            <div className="mt-1 text-[11px] text-slate-600">{anchorDetail.linkedEventId}</div>
          </div>
        ) : null}
      </div>
    );
  };

  const renderNeighborhood = () => {
    if (loading) {
      return <div className="text-xs text-slate-500">Loading related items…</div>;
    }

    const neighborhood = workroomContext?.neighborhood;
    if (!neighborhood) {
      return (
        <div className="rounded border border-dashed border-slate-200 bg-slate-50 p-3 text-xs text-slate-600">
          No nearby context yet. Ask the assistant to pull in related items.
        </div>
      );
    }

    return (
      <div className="space-y-3 text-xs text-slate-700">
        {neighborhood.tasks?.length ? (
          <div>
            <div className="text-[11px] font-semibold text-slate-600">Tasks</div>
            <div className="mt-1 flex flex-col gap-1">
              {neighborhood.tasks.map((task) => (
                <div key={task.id} className="flex items-center justify-between rounded border border-slate-200 bg-white px-2 py-1">
                  <span className="truncate text-[12px] font-medium">{task.title || task.id}</span>
                  {task.status && (
                    <span className="rounded-full bg-slate-50 px-2 py-1 text-[11px] font-medium text-slate-700">
                      {statusLabelMap[task.status] || task.status}
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        ) : null}

        {neighborhood.events?.length ? (
          <div>
            <div className="text-[11px] font-semibold text-slate-600">Events</div>
            <div className="mt-1 flex flex-col gap-1">
              {neighborhood.events.map((event) => (
                <div key={event.id} className="rounded border border-slate-200 bg-white px-2 py-1">
                  <div className="text-[12px] font-medium">{event.title || event.id}</div>
                  <div className="text-[11px] text-slate-500">
                    {formatTimeWindow(event.start, event.end)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : null}

        {neighborhood.docs?.length ? (
          <div>
            <div className="text-[11px] font-semibold text-slate-600">Docs</div>
            <div className="mt-1 flex flex-col gap-1">
              {neighborhood.docs.map((doc) => (
                <div key={doc.id} className="rounded border border-slate-200 bg-white px-2 py-1 text-[12px] text-slate-700">
                  {doc.title || doc.id}
                </div>
              ))}
            </div>
          </div>
        ) : null}

        {neighborhood.queueItems?.length ? (
          <div>
            <div className="text-[11px] font-semibold text-slate-600">Queue</div>
            <div className="mt-1 flex flex-col gap-1">
              {neighborhood.queueItems.map((item) => (
                <div key={item.id} className="rounded border border-slate-200 bg-white px-2 py-1 text-[12px] text-slate-700">
                  {item.subject || item.id}
                </div>
              ))}
            </div>
          </div>
        ) : null}

        {!neighborhood.tasks?.length &&
          !neighborhood.events?.length &&
          !neighborhood.docs?.length &&
          !neighborhood.queueItems?.length && (
            <div className="rounded border border-dashed border-slate-200 bg-slate-50 p-3 text-xs text-slate-600">
              No neighborhood suggestions yet.
            </div>
          )}
      </div>
    );
  };

  return (
    <div className="flex flex-col gap-3 rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Context</div>
          <div className="text-sm font-bold text-slate-800">{headerLabel}</div>
        </div>
        <div className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
          Mode: {current.mode}
        </div>
      </div>

      <div className="flex gap-2 text-xs font-medium text-slate-600">
        {(
          [
            { id: "focus", label: "Focus" },
            { id: "notes", label: "Notes" },
            { id: "neighborhood", label: "Neighborhood" },
          ] as Array<{ id: TabKey; label: string }>
        ).map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`rounded-md px-3 py-1 transition-colors ${
              activeTab === tab.id
                ? "bg-slate-900 text-white"
                : "bg-slate-100 text-slate-700 hover:bg-slate-200"
            }`}
            type="button"
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === "focus" && renderFocusSummary()}

      {activeTab === "notes" && (
        <div className="space-y-2 text-xs text-slate-700">
          <label className="text-[11px] font-semibold text-slate-600" htmlFor="context-notes">
            Notes for this focus
          </label>
          <textarea
            id="context-notes"
            value={noteValue}
            onChange={(e) => handleNoteChange(e.target.value)}
            placeholder="Capture constraints, links, or reminders the assistant should keep in mind."
            className="min-h-[120px] w-full rounded-md border border-slate-200 p-2 text-sm text-slate-800 shadow-inner focus:border-slate-400 focus:outline-none"
          />
          <div className="text-[11px] text-slate-500">Saved locally per focus; share with the assistant when ready.</div>
        </div>
      )}

      {activeTab === "neighborhood" && renderNeighborhood()}
    </div>
  );
}


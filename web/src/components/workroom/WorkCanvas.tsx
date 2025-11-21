import { useMemo } from "react";
import { AssistantChat } from "../hub/AssistantChat";
import { useFocusContextStore } from "../../state/focusContextStore";
import { WorkBoard } from "./WorkBoard";
import { formatTimeWindow, statusLabelMap } from "../../data/mockWorkroomData";
import { useWorkroomContext } from "../../hooks/useWorkroomContext";
import type { WorkroomContextAnchor, WorkroomContext } from "../../lib/workroomContext";
import type { SurfaceNavigateTo } from "../../lib/llm/surfaces";

export function WorkCanvas() {
  const { current, pushFocus } = useFocusContextStore();
  const { workroomContext, loading, error } = useWorkroomContext();

  const chatContextId = useMemo(() => {
    if (!current) return "";
    const anchorId = current.anchor.id || current.anchor.type;
    return `${current.anchor.type}:${anchorId}`;
  }, [current]);

  if (!current) {
    return (
      <div className="p-6 text-slate-500">Select a focus to get started.</div>
    );
  }

  if (current.anchor.type === "portfolio" || current.anchor.type === "project") {
    const emphasis =
      current.mode === "plan"
        ? "You are planning your work."
        : current.mode === "execute"
          ? "You are executing your work."
          : "You are reviewing your work.";
    const contextAnchor = workroomContext?.anchor;
    const anchorLabel =
      contextAnchor?.type === "portfolio"
        ? contextAnchor.label
        : contextAnchor?.type === "project"
          ? contextAnchor.name
          : undefined;
    return (
      <div className="flex h-full flex-col gap-3">
        <div className="px-4 pt-4 text-sm text-slate-600">
          {emphasis}
          {anchorLabel && (
            <div className="text-xs text-slate-500">Viewing {anchorLabel}</div>
          )}
        </div>
        <WorkBoard boardType={current.anchor.type} anchor={current.anchor} />
      </div>
    );
  }

  const headerAnchor = workroomContext?.anchor;

  const anchorForDisplay: WorkroomContextAnchor | null =
    headerAnchor ||
    (current.anchor.type === "task" && current.anchor.id
      ? { type: "task", id: current.anchor.id, title: current.anchor.id }
      : current.anchor.type === "event" && current.anchor.id
        ? { type: "event", id: current.anchor.id, title: current.anchor.id }
        : null);

  const resolveTitle = (anchor?: WorkroomContextAnchor | null) => {
    if (!anchor) return current.anchor.id || current.anchor.type;
    if (anchor.type === "task" || anchor.type === "event") {
      return anchor.title;
    }
    if (anchor.type === "project") return anchor.name;
    if (anchor.type === "portfolio") return anchor.label;
    return current.anchor.id || current.anchor.type;
  };

  const resolveStatus = (anchor?: WorkroomContextAnchor | null) => {
    if (anchor?.type === "task" && anchor.status) {
      return statusLabelMap[anchor.status] || anchor.status;
    }
    return undefined;
  };

  const resolvePriority = (anchor?: WorkroomContextAnchor | null) => {
    if (anchor?.type === "task") return anchor.priority;
    return undefined;
  };

  const resolveDetail = (
    anchor?: WorkroomContextAnchor | null,
    ctx?: WorkroomContext | null
  ) => {
    if (!anchor) return "";
    if (anchor.type === "event") {
      return formatTimeWindow(anchor.start, anchor.end);
    }
    if (anchor.type === "task") {
      if (anchor.linkedEventId) {
        const linkedEvent = ctx?.neighborhood?.events?.find(
          (event) => event.id === anchor.linkedEventId
        );
        if (linkedEvent) return `Linked to: ${linkedEvent.title}`;
      }
      return formatTimeWindow();
    }
    return "";
  };

  const headerTitle = resolveTitle(anchorForDisplay ?? headerAnchor);
  const headerStatus = resolveStatus(anchorForDisplay ?? headerAnchor);
  const headerPriority = resolvePriority(anchorForDisplay ?? headerAnchor);
  const anchorDetail = resolveDetail(anchorForDisplay ?? headerAnchor, workroomContext);
  const headerNote = loading ? "Loading context..." : error ? "Context unavailable" : null;

  const surfacesEnabled =
    (current.anchor.type === "task" || current.anchor.type === "event") &&
    current.mode === "execute";

  const handleSurfaceNavigate = (nav: SurfaceNavigateTo) => {
    if (nav.destination === "workroom_task") {
      pushFocus({ type: "task", id: nav.taskId }, { source: "direct" });
      return;
    }
    if (nav.destination === "calendar_event") {
      pushFocus({ type: "event", id: nav.eventId }, { source: "direct" });
    }
  };

  return (
    <div className="flex h-full flex-col gap-4 p-4">
      <div className="flex items-center justify-between rounded-lg border border-slate-200 bg-white p-3">
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2 text-sm text-slate-600">
            <span className="rounded-full bg-blue-50 px-3 py-1 text-blue-700">
              {current.anchor.type.toUpperCase()}
            </span>
            <span className="font-semibold text-slate-800">{headerTitle}</span>
          </div>
          <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500">
            {headerStatus && (
              <span className="rounded-full bg-slate-100 px-2 py-1 font-medium text-slate-700">
                Status: {headerStatus}
              </span>
            )}
            {headerPriority && (
              <span className="rounded-full bg-amber-50 px-2 py-1 font-medium text-amber-800">
                Priority: {headerPriority}
              </span>
            )}
            <span className="rounded-full bg-slate-50 px-2 py-1 font-medium text-slate-700">
              {anchorDetail}
            </span>
            {headerNote && <span className="text-slate-400">{headerNote}</span>}
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-hidden rounded-xl border border-slate-200 bg-white">
        <AssistantChat
          actionId={chatContextId}
          taskId={current.anchor.id}
          mode="workroom"
          shouldFocus={false}
          surfaceRenderAllowed={surfacesEnabled}
          onSurfaceNavigateOverride={handleSurfaceNavigate}
        />
      </div>

      {current.mode === "plan" && (
        <div className="rounded-lg border border-slate-200 bg-white p-4">
          <div className="mb-2 text-sm font-semibold text-slate-800">Planning</div>
          <div className="rounded border border-dashed border-slate-200 bg-slate-50 p-3 text-sm text-slate-600">
            Planning surface: schedule and options will appear here.
          </div>
        </div>
      )}

      {current.mode === "execute" && (
        <div className="rounded-lg border border-slate-200 bg-white p-4">
          <div className="mb-2 text-sm font-semibold text-slate-800">Execution</div>
          <div className="rounded border border-dashed border-slate-200 bg-slate-50 p-3 text-sm text-slate-600">
            Focus next: prioritized actions will appear here.
          </div>
        </div>
      )}

      {current.mode === "review" && (
        <div className="rounded-lg border border-slate-200 bg-white p-4">
          <div className="mb-2 text-sm font-semibold text-slate-800">Review</div>
          <div className="rounded border border-dashed border-slate-200 bg-slate-50 p-3 text-sm text-slate-600">
            Activity timeline: history and outcomes will appear here.
          </div>
        </div>
      )}
    </div>
  );
}

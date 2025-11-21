import { Text } from "@lucid-work/ui";
import { useMemo } from "react";
import { useFocusContextStore } from "../../state/focusContextStore";
import type { FocusAnchorType } from "../../lib/focusContext";
import { useWorkroomContext } from "../../hooks/useWorkroomContext";

export function NeighborhoodRail() {
  const { pushFocus } = useFocusContextStore();
  const { workroomContext, loading, error } = useWorkroomContext();

  const neighborhood = useMemo(() => workroomContext?.neighborhood, [workroomContext]);

  const renderItems = (
    label: string,
    items?: Array<{ id: string; title: string }>,
    type?: FocusAnchorType
  ) => {
    if (!items || items.length === 0) return null;
    return (
      <div className="flex flex-col gap-2">
        <Text variant="caption" className="text-xs font-semibold uppercase text-slate-500">
          {label}
        </Text>
        <div className="flex flex-col gap-1">
          {items.map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() =>
                pushFocus({ type: (type || "task") as FocusAnchorType, id: item.id }, { source: "direct" })
              }
              className="w-full rounded border border-slate-200 bg-slate-50 px-3 py-2 text-left text-sm font-medium text-slate-700 transition hover:bg-white hover:shadow-sm"
            >
              {item.title}
            </button>
          ))}
        </div>
      </div>
    );
  };

  const hasContent =
    (neighborhood?.tasks?.length || 0) > 0 ||
    (neighborhood?.events?.length || 0) > 0 ||
    (neighborhood?.docs?.length || 0) > 0 ||
    (neighborhood?.queueItems?.length || 0) > 0;

  return (
    <div className="flex h-full flex-col gap-4 rounded-lg border border-slate-200 bg-white p-3 text-sm text-slate-500">
      <Text variant="body" className="text-sm font-semibold text-slate-700">
        Neighborhood
      </Text>

      {loading ? (
        <Text variant="caption" className="text-xs text-slate-500">
          Loading related items...
        </Text>
      ) : hasContent ? (
        <div className="flex flex-col gap-4">
          {renderItems("Related tasks", neighborhood?.tasks, "task")}
          {renderItems("Related events", neighborhood?.events, "event")}
          {renderItems("Related docs", neighborhood?.docs)}
          {renderItems("Related inbox items", neighborhood?.queueItems?.map(item => ({ id: item.id, title: item.subject })))}
        </div>
      ) : (
        <Text variant="caption" className="text-xs text-slate-500">
          {error ? "Context unavailable" : "No related items"}
        </Text>
      )}
    </div>
  );
}

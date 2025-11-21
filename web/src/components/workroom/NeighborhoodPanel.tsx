import { Text } from "@ygt-assistant/ui";
import { useMemo } from "react";
import { useFocusContextStore } from "../../state/focusContextStore";
import type { FocusAnchorType } from "../../lib/focusContext";
import { useWorkroomContext } from "../../hooks/useWorkroomContext";

export function NeighborhoodPanel() {
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

  if (loading) {
    return (
      <Text variant="caption" className="text-xs text-slate-500">
        Loading related items...
      </Text>
    );
  }

  if (!hasContent) {
    return (
      <Text variant="caption" className="text-xs text-slate-500">
        {error ? "Context unavailable" : "No related items"}
      </Text>
    );
  }

  return (
    <div className="flex flex-col gap-4 text-sm text-slate-500" data-testid="neighborhood-panel">
      {renderItems("Related tasks", neighborhood?.tasks, "task")}
      {renderItems("Related events", neighborhood?.events, "event")}
      {renderItems("Related docs", neighborhood?.docs)}
      {renderItems(
        "Related inbox items",
        neighborhood?.queueItems?.map((item) => ({ id: item.id, title: item.subject }))
      )}
    </div>
  );
}

import { useEffect, useMemo, useState } from "react";
import { Button } from "@lucid-work/ui/primitives/Button";
import { Text } from "@lucid-work/ui";
import { ChevronLeft24Regular } from "@fluentui/react-icons";
import { useFocusContextStore } from "../../state/focusContextStore";
import type { FocusContext, FocusMode } from "../../lib/focusContext";

const originLabelMap: Record<string, string> = {
  hub_surface: "From: Hub",
  board: "From: Board",
  direct: "Direct entry",
};

const modeLabels: FocusMode[] = ["plan", "execute", "review"];

const formatAnchorTitle = (ctx?: FocusContext) => {
  if (!ctx) return "";
  const { anchor } = ctx;
  const titleFromNeighborhood = ctx.neighborhood?.tasks?.find(
    (task) => task.id === anchor.id
  )?.title;

  switch (anchor.type) {
    case "portfolio":
      if (anchor.id === "my_work") {
        return "My work · Board view";
      }
      return `Portfolio: ${anchor.id || "untitled"} · Board view`;
    case "project":
      return `Project: ${anchor.id || "untitled"} · Board view`;
    case "task":
      return `Task: ${titleFromNeighborhood || anchor.id || "untitled"}`;
    case "event":
      return `Meeting: ${titleFromNeighborhood || anchor.id || "untitled"}`;
    default:
      return "";
  }
};

export function WorkroomAnchorBar() {
  const { current, stack, updateFocusMode, popFocus } = useFocusContextStore();
  const [clock, setClock] = useState<string>("");

  useEffect(() => {
    const updateClock = () => {
      setClock(new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }));
    };
    updateClock();
    const interval = setInterval(updateClock, 60_000);
    return () => clearInterval(interval);
  }, []);

  const anchorTitle = useMemo(() => formatAnchorTitle(current), [current]);
  const originLabel = useMemo(() => {
    if (!current?.origin) return "";
    if (current.origin.source === "board") {
      if (current.origin.surfaceKind === "my_work") {
        return "From: My work board";
      }
      if (current.origin.surfaceKind === "project_board") {
        return "From: Project board";
      }
      return originLabelMap[current.origin.source];
    }
    if (current.origin.source === "hub_surface") {
      return originLabelMap[current.origin.source];
    }
    if (current.origin.source === "direct") {
      return "";
    }
    return originLabelMap[current.origin.source] || "";
  }, [current]);

  const handleModeChange = (mode: FocusMode) => {
    updateFocusMode(mode);
  };

  return (
    <div className="flex items-center justify-between border-b border-slate-200 bg-white px-4 py-3 shadow-sm">
      <div className="flex items-center gap-3">
        {stack.length > 0 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={popFocus}
            className="flex items-center gap-1"
          >
            <ChevronLeft24Regular />
            Back
          </Button>
        )}
        <div className="flex flex-col">
          <Text variant="caption" className="text-xs text-slate-500">
            {originLabel || "Focus"}
          </Text>
          <Text variant="body" className="text-base font-semibold">
            {anchorTitle}
          </Text>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="text-sm text-slate-500">
          <span className="font-medium text-slate-700">Now</span> · {clock || "--:--"}
        </div>
        <div className="flex items-center gap-2 rounded-full bg-slate-100 px-2 py-1">
          {modeLabels.map((mode) => {
            const isActive = current?.mode === mode;
            return (
              <Button
                key={mode}
                size="sm"
                variant={isActive ? "solid" : "ghost"}
                onClick={() => handleModeChange(mode)}
                className={`rounded-full px-3 text-xs ${
                  isActive ? "bg-blue-600 text-white" : "text-slate-600"
                }`}
              >
                {mode.charAt(0).toUpperCase() + mode.slice(1)}
              </Button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

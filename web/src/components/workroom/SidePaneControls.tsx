import { Button } from "@lucid-work/ui/primitives/Button";
import {
  PanelLeft24Regular,
  PanelRight24Regular,
} from "@fluentui/react-icons";

interface SidePaneControlsProps {
  primaryView: "workroom" | "kanban";
  navOpen: boolean;
  contextOpen: boolean;
  onToggleNav: () => void;
  onToggleContext: () => void;
}

export function SidePaneControls({
  primaryView,
  navOpen,
  contextOpen,
  onToggleNav,
  onToggleContext,
}: SidePaneControlsProps) {
  const navDisabled = primaryView === "kanban";
  const contextDisabled = primaryView === "kanban";

  return (
    <div className="flex items-center justify-between px-4 py-1.5 border-b border-slate-100 bg-slate-50">
      {/* Left: Nav toggle */}
      <Button
        variant="ghost"
        size="sm"
        onClick={onToggleNav}
        disabled={navDisabled}
        className="h-7 px-2"
        aria-pressed={navOpen}
        aria-label={navDisabled ? "Unavailable in Kanban" : "Toggle Navigator (⌥N)"}
        title={navDisabled ? "Unavailable in Kanban" : "Toggle Navigator (⌥N)"}
      >
        <PanelLeft24Regular className="w-4 h-4" />
      </Button>

      {/* Right: Context toggle */}
      <Button
        variant="ghost"
        size="sm"
        onClick={onToggleContext}
        disabled={contextDisabled}
        className="h-7 px-2"
        aria-pressed={contextOpen}
        aria-label={contextDisabled ? "Unavailable in Kanban" : "Toggle Context (⌥C)"}
        title={contextDisabled ? "Unavailable in Kanban" : "Toggle Context (⌥C)"}
      >
        <PanelRight24Regular className="w-4 h-4" />
      </Button>
    </div>
  );
}


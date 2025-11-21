import { Button } from "@lucid-work/ui/primitives/Button";
import type { PrimaryView } from "../../hooks/useWorkroomStore";

interface ViewSwitcherProps {
  value: PrimaryView;
  onChange: (view: PrimaryView) => void;
}

export function ViewSwitcher({ value, onChange }: ViewSwitcherProps) {
  return (
    <div className="inline-flex rounded-lg border border-slate-200 bg-slate-50 p-1">
      <button
        onClick={() => onChange("workroom")}
        className={`px-3 py-1 text-sm font-medium rounded transition-colors ${
          value === "workroom"
            ? "bg-white text-slate-900 shadow-sm"
            : "text-slate-600 hover:text-slate-900"
        }`}
        aria-pressed={value === "workroom"}
      >
        Workroom
      </button>
      <button
        onClick={() => onChange("kanban")}
        className={`px-3 py-1 text-sm font-medium rounded transition-colors ${
          value === "kanban"
            ? "bg-white text-slate-900 shadow-sm"
            : "text-slate-600 hover:text-slate-900"
        }`}
        aria-pressed={value === "kanban"}
      >
        Kanban
      </button>
    </div>
  );
}


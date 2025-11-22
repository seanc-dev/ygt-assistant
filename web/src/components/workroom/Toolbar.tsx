import { Button } from "@lucid-work/ui/primitives/Button";
import {
  Calendar24Regular,
  Attach24Regular,
  Board24Regular,
} from "@fluentui/react-icons";
import type { TaskStatus } from "../../hooks/useWorkroomStore";

interface ToolbarProps {
  taskId: string;
  status: TaskStatus;
  onStatusChange: (status: TaskStatus) => void;
  onOpenKanban?: () => void;
}

export function Toolbar({
  taskId,
  status,
  onStatusChange,
  onOpenKanban,
}: ToolbarProps) {
  const statusOptions: { value: TaskStatus; label: string }[] = [
    { value: "backlog", label: "Backlog" },
    { value: "ready", label: "Ready" },
    { value: "doing", label: "Doing" },
    { value: "blocked", label: "Blocked" },
    { value: "done", label: "Done" },
  ];

  return (
    <div className="flex items-center gap-2 p-2 border-b border-slate-100 bg-white">
      <Button variant="ghost" size="sm" onClick={() => {}}>
        <Calendar24Regular className="w-3.5 h-3.5 mr-1" />
        Add focus block
      </Button>

      <Button variant="ghost" size="sm" onClick={() => {}}>
        <Attach24Regular className="w-3.5 h-3.5 mr-1" />
        Attach source
      </Button>

      <select
        value={status}
        onChange={(e) => onStatusChange(e.target.value as TaskStatus)}
        className="text-xs border border-slate-200 rounded px-2 py-1 bg-white hover:bg-slate-50"
      >
        {statusOptions.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>

      {onOpenKanban && (
        <Button variant="ghost" size="sm" onClick={onOpenKanban}>
          <Board24Regular className="w-3.5 h-3.5 mr-1" />
          Open Kanban
        </Button>
      )}
    </div>
  );
}

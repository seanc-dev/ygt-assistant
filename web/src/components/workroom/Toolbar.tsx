import { useState } from "react";
import { Button } from "@ygt-assistant/ui";
import {
  Play24Regular,
  Calendar24Regular,
  Attach24Regular,
} from "@fluentui/react-icons";
import { SlashMenu, type SlashCommand } from "../ui/SlashMenu";
import type { TaskStatus } from "../../hooks/useWorkroomStore";

interface ToolbarProps {
  taskId: string;
  status: TaskStatus;
  onStatusChange: (status: TaskStatus) => void;
  onSlashMenuOpen: () => void;
}

export function Toolbar({
  taskId,
  status,
  onStatusChange,
  onSlashMenuOpen,
}: ToolbarProps) {
  const statusOptions: { value: TaskStatus; label: string }[] = [
    { value: "backlog", label: "Backlog" },
    { value: "ready", label: "Ready" },
    { value: "doing", label: "Doing" },
    { value: "blocked", label: "Blocked" },
    { value: "done", label: "Done" },
  ];

  return (
    <div className="flex items-center gap-2 p-2 border-b border-slate-200">
      <Button variant="solid" size="sm" onClick={onSlashMenuOpen}>
        <Play24Regular className="w-4 h-4 mr-1" />
        Run
      </Button>

      <select
        value={status}
        onChange={(e) => onStatusChange(e.target.value as TaskStatus)}
        className="text-xs border rounded px-2 py-1"
      >
        {statusOptions.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>

      <Button variant="outline" size="sm">
        <Calendar24Regular className="w-4 h-4 mr-1" />
        Add focus block
      </Button>

      <Button variant="outline" size="sm">
        <Attach24Regular className="w-4 h-4 mr-1" />
        Attach source
      </Button>
    </div>
  );
}


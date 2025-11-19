import { useState, useRef, useEffect } from "react";
import {
  Document24Regular,
  Mail24Regular,
  Calendar24Regular,
  Code24Regular,
  Link24Regular,
  List24Regular,
  Clock24Regular,
} from "@fluentui/react-icons";

export interface SlashCommand {
  id: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  description: string;
  prompt?: string;
  requiresParams?: boolean;
}

const defaultCommands: SlashCommand[] = [
  {
    id: "draft-email",
    label: "Draft email",
    icon: Mail24Regular,
    description: "Compose an email draft",
    prompt: "Draft an email",
  },
  {
    id: "summarize-doc",
    label: "Summarize doc",
    icon: Document24Regular,
    description: "Create a summary of the current document",
    prompt: "Summarize this document",
  },
  {
    id: "generate-plan",
    label: "Generate plan",
    icon: List24Regular,
    description: "Create an action plan",
    prompt: "Generate a plan for",
  },
  {
    id: "create-subtasks",
    label: "Create sub-tasks",
    icon: List24Regular,
    description: "Break down into sub-tasks",
    prompt: "Create sub-tasks for",
  },
  {
    id: "schedule-focus",
    label: "Schedule focus block",
    icon: Clock24Regular,
    description: "Add a focused work session",
    prompt: "Schedule a focus block for",
  },
  {
    id: "add-calendar-event",
    label: "Add calendar event",
    icon: Calendar24Regular,
    description: "Create a calendar event",
    prompt: "Add calendar event",
  },
  {
    id: "link-file",
    label: "Link file",
    icon: Link24Regular,
    description: "Attach or link a file",
    prompt: "Link file",
  },
  {
    id: "insert-citation",
    label: "Insert citation",
    icon: Document24Regular,
    description: "Add a reference citation",
    prompt: "Insert citation",
  },
  {
    id: "create-doc-outline",
    label: "Create Task Doc outline",
    icon: Document24Regular,
    description: "Generate document structure",
    prompt: "Create Task Doc outline",
  },
  {
    id: "insert-code-diff",
    label: "Insert code diff",
    icon: Code24Regular,
    description: "Add a code change preview",
    prompt: "Insert code diff",
  },
];

interface SlashMenuProps {
  onSelect: (command: SlashCommand) => void;
  onClose: () => void;
  position: { top: number; left: number };
  commands?: SlashCommand[];
}

export function SlashMenu({
  onSelect,
  onClose,
  position,
  commands: customCommands,
}: SlashMenuProps) {
  const [selectedIndex, setSelectedIndex] = useState(0);
  const menuRef = useRef<HTMLDivElement>(null);
  const menuCommands = customCommands ?? defaultCommands;
  const lastIndex = Math.max(menuCommands.length - 1, 0);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setSelectedIndex((prev) => Math.min(prev + 1, lastIndex));
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setSelectedIndex((prev) => Math.max(prev - 1, 0));
      } else if (e.key === "Enter") {
        e.preventDefault();
        onSelect(menuCommands[selectedIndex]);
      } else if (e.key === "Escape") {
        e.preventDefault();
        onClose();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [selectedIndex, onSelect, onClose, menuCommands, lastIndex]);

  useEffect(() => {
    // Scroll selected item into view
    const selectedElement = menuRef.current?.children[
      selectedIndex
    ] as HTMLElement;
    if (selectedElement) {
      selectedElement.scrollIntoView({ block: "nearest" });
    }
  }, [selectedIndex]);

  useEffect(() => {
    setSelectedIndex(0);
  }, [menuCommands]);

  return (
    <div
      ref={menuRef}
      className="absolute z-50 bg-white border border-slate-200 rounded-lg shadow-lg max-h-80 overflow-y-auto"
      style={{
        top: position.top,
        left: position.left,
        minWidth: "280px",
      }}
    >
      {menuCommands.map((cmd, index) => {
        const Icon = cmd.icon;
        const isSelected = index === selectedIndex;
        return (
          <button
            key={cmd.id}
            onClick={() => onSelect(cmd)}
            className={`w-full flex items-center gap-3 px-3 py-2 text-left hover:bg-slate-50 transition-colors ${
              isSelected ? "bg-slate-100" : ""
            }`}
          >
            <Icon className="w-5 h-5 text-slate-600 flex-shrink-0" />
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium text-slate-900">
                {cmd.label}
              </div>
              <div className="text-xs text-slate-500">{cmd.description}</div>
            </div>
          </button>
        );
      })}
    </div>
  );
}


import { Button } from "@ygt-assistant/ui/primitives/Button";
import {
  Document24Regular,
  Chat24Regular,
  History24Regular,
} from "@fluentui/react-icons";
import type { View } from "../../hooks/useWorkroomStore";

interface ModeTabsProps {
  view: View;
  onViewChange: (view: View) => void;
  taskId?: string;
  chatCount?: number;
}

export function ModeTabs({
  view,
  onViewChange,
  taskId,
  chatCount = 0,
}: ModeTabsProps) {
  const tabs: { id: View; label: string; icon: typeof Document24Regular }[] = [
    { id: "doc", label: "Doc", icon: Document24Regular },
    { id: "chats", label: "Chats", icon: Chat24Regular },
    { id: "activity", label: "Activity", icon: History24Regular },
  ];

  return (
    <div className="flex items-center justify-between border-b border-slate-200 bg-white">
      <div className="flex items-center">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = view === tab.id;
          const showCount = tab.id === "chats" && chatCount > 0;

          return (
            <button
              key={tab.id}
              onClick={() => {
                if (taskId) {
                  onViewChange(tab.id);
                }
              }}
              disabled={!taskId}
              className={`flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                isActive
                  ? "border-sky-500 text-slate-900"
                  : "border-transparent text-slate-600 hover:text-slate-800"
              } ${!taskId ? "opacity-50 cursor-not-allowed" : ""}`}
            >
              <Icon className="w-4 h-4" />
              <span>{tab.label}</span>
              {showCount && (
                <span className="bg-slate-200 text-slate-700 text-xs rounded-full px-1.5 py-0.5">
                  {chatCount}
                </span>
              )}
            </button>
          );
        })}
      </div>

    </div>
  );
}


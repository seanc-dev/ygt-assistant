import { useWorkroomStore } from "../../hooks/useWorkroomStore";
import { useMemo } from "react";

interface Props {
  view: "doc" | "chats" | "activity" | "kanban";
  taskTitle?: string;
  breadcrumb?: string[];
  onChangeView: (v: Props["view"]) => void;
}

export function WorkroomHeader({ view, taskTitle, breadcrumb = [], onChangeView }: Props) {
  const isKanban = view === "kanban";
  const bc = useMemo(() => breadcrumb.filter(Boolean).join(" ▸ "), [breadcrumb]);

  const viewLabels: Record<string, string> = {
    doc: "Task",
    chats: "Chats",
    activity: "Activity",
    kanban: "Kanban",
  };

  return (
    <div className="flex items-center justify-between px-4 border-b border-slate-200 h-12">
      <div className="flex items-center gap-2">
        <div className="inline-flex rounded-md bg-slate-50 p-1">
          {["doc","chats","activity","kanban"].map((k) => (
            <button
              key={k}
              onClick={() => onChangeView(k as any)}
              className={`px-3 py-1.5 text-sm rounded transition-colors ${view===k ? "bg-white shadow-sm border border-slate-200" : "text-slate-600 hover:text-slate-900"}`}
            >
              {viewLabels[k]}
            </button>
          ))}
        </div>
        {!isKanban && (
          <div className="ml-3 text-sm text-slate-500 truncate max-w-[40vw]">
            {bc && <span className="mr-2">{bc}</span>}
            {taskTitle && <span className="text-slate-900 font-medium">{taskTitle}</span>}
          </div>
        )}
      </div>
      {/* No panel toggles here. Keep header minimal. */}
      <div className="h-10" />
    </div>
  );
}


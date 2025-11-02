import { ReactNode } from "react";

interface ScheduleDayViewProps {
  events: Array<{
    id: string;
    title: string;
    start: string;
    end: string;
    link?: string;
  }>;
  blocks: Array<{
    id: string;
    kind: "focus" | "admin" | "meeting";
    tasks: string[];
    start: string;
    end: string;
    priority: string;
  }>;
  onEditInChat: (blockId: string) => void;
  expandedBlockId: string | null;
}

export function ScheduleDayView({
  events,
  blocks,
  onEditInChat,
  expandedBlockId,
}: ScheduleDayViewProps) {
  // Combine events and blocks, sort by start time
  const allItems = [
    ...events.map((e) => ({ ...e, type: "event" as const })),
    ...blocks.map((b) => ({ ...b, type: "block" as const })),
  ].sort((a, b) => new Date(a.start).getTime() - new Date(b.start).getTime());

  const formatTime = (iso: string) => {
    const date = new Date(iso);
    return date.toLocaleTimeString("en-US", {
      hour: "numeric",
      minute: "2-digit",
    });
  };

  return (
    <div className="space-y-2">
      {allItems.length === 0 ? (
        <div className="text-sm text-gray-500">No events or blocks scheduled</div>
      ) : (
        allItems.map((item) => (
          <div
            key={item.id}
            className={`rounded-lg border p-4 ${
              item.type === "event"
                ? "bg-blue-50 border-blue-200"
                : item.type === "block"
                ? "bg-green-50 border-green-200"
                : ""
            }`}
          >
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium text-sm">
                  {item.type === "event" ? item.title : `${item.kind} block`}
                </div>
                <div className="text-xs text-gray-600">
                  {formatTime(item.start)} - {formatTime(item.end)}
                </div>
                {item.type === "block" && item.tasks.length > 0 && (
                  <div className="text-xs text-gray-500 mt-1">
                    Tasks: {item.tasks.join(", ")}
                  </div>
                )}
              </div>
              {item.type === "block" && (
                <button
                  onClick={() => onEditInChat(item.id)}
                  className="text-xs text-blue-600 hover:text-blue-800"
                >
                  Edit in Chat
                </button>
              )}
            </div>
          </div>
        ))
      )}
    </div>
  );
}

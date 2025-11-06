import { Calendar24Regular, List24Regular } from "@fluentui/react-icons";
import { useRouter } from "next/router";
import { useCallback } from "react";

type TodayItem = {
  id: string;
  title: string;
  due: string | null;
  source: "queue" | "calendar";
  priority: "low" | "med" | "high";
};

interface WorkloadTodayProps {
  items: TodayItem[];
}

/**
 * Display today's focus items as chips.
 * Clicking opens the item in its source context.
 */
export function WorkloadToday({ items }: WorkloadTodayProps) {
  const router = useRouter();
  
  const handleItemClick = useCallback((item: TodayItem) => {
    if (item.source === "queue") {
      // Navigate to action queue and highlight item
      router.push("/hub#action-" + item.id);
    } else if (item.source === "calendar") {
      // Navigate to schedule and highlight item
      router.push("/hub#schedule-" + item.id);
    }
  }, [router]);
  
  if (items.length === 0) {
    return (
      <div className="text-center py-4">
        <p className="text-sm text-slate-500">No planned work for today</p>
      </div>
    );
  }
  
  return (
    <div className="flex flex-wrap gap-2">
      {items.map((item) => {
        const Icon = item.source === "calendar" ? Calendar24Regular : List24Regular;
        const priorityColors = {
          high: "bg-rose-100 text-rose-700 border-rose-200",
          med: "bg-amber-100 text-amber-700 border-amber-200",
          low: "bg-slate-100 text-slate-600 border-slate-200",
        };
        
        return (
          <button
            key={item.id}
            onClick={() => handleItemClick(item)}
            className={`
              inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium
              border transition-colors hover:opacity-80 focus:outline-none focus:ring-2
              focus:ring-sky-500 focus:ring-offset-1
              ${priorityColors[item.priority]}
            `}
            title={item.title}
            aria-label={`${item.title} (${item.source}, ${item.priority} priority)`}
          >
            <Icon className="w-3.5 h-3.5 flex-shrink-0" />
            <span className="truncate max-w-[120px]">{item.title}</span>
          </button>
        );
      })}
    </div>
  );
}


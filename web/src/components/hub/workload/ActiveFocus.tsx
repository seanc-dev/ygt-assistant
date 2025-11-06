import { Calendar24Regular, ClipboardTask24Regular, Sparkle24Regular } from "@fluentui/react-icons";
import { useRouter } from "next/router";
import { useCallback } from "react";
import type { FocusItem } from "../../../lib/workload";

interface ActiveFocusProps {
  items: FocusItem[];
}

/**
 * Display active focus items as a muted list.
 * Urgent items show amber bullets; others are neutral.
 */
export function ActiveFocus({ items }: ActiveFocusProps) {
  const router = useRouter();
  
  const handleItemClick = useCallback((item: FocusItem) => {
    if (item.source === "calendar") {
      router.push("/hub#schedule-" + item.id);
    } else if (item.source === "task") {
      router.push("/hub#action-" + item.id);
    } else {
      // AI/suggested items
      router.push("/hub#ai-" + item.id);
    }
  }, [router]);
  
  const getIcon = (source: FocusItem["source"]) => {
    switch (source) {
      case "calendar":
        return Calendar24Regular;
      case "task":
        return ClipboardTask24Regular;
      case "ai":
        return Sparkle24Regular;
    }
  };
  
  if (items.length === 0) {
    return (
      <div className="mt-2 text-sm text-slate-500">
        No active focus items
      </div>
    );
  }
  
  return (
    <div className="mt-2 space-y-1">
      {items.map((item) => {
        const Icon = getIcon(item.source);
        const isUrgent = item.urgent;
        
        return (
          <button
            key={item.id}
            onClick={() => handleItemClick(item)}
            className={`
              flex items-center gap-2 text-sm w-full text-left
              hover:bg-slate-100 rounded-md px-2 py-1 transition
              focus:outline-none focus:ring-2 focus:ring-sky-500 focus:ring-offset-1
              ${isUrgent ? "text-slate-900" : "text-slate-800"}
            `}
            aria-label={`${item.title} (${item.source}${isUrgent ? ", urgent" : ""})`}
          >
            {/* Bullet */}
            <div
              className={`
                h-1.5 w-1.5 rounded-full flex-shrink-0
                ${isUrgent ? "bg-amber-500" : "bg-slate-400"}
              `}
            />
            
            {/* Icon */}
            <Icon className="w-4 h-4 flex-shrink-0 text-slate-400" />
            
            {/* Title */}
            <span className="truncate flex-1">{item.title}</span>
          </button>
        );
      })}
    </div>
  );
}


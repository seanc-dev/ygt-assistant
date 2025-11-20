import { useState, useRef } from "react";
import {
  formatTime,
  formatTimeRange,
  isPast,
  getAccentColor,
  hasOverlap,
  type ScheduleItem,
} from "../../lib/schedule";
import { OverflowMenu, OverflowMenuItem } from "./OverflowMenu";
import { SmartCommandInput } from "./SmartCommandInput";
import {
  Copy24Regular,
  Delete24Regular,
  MoreHorizontal24Regular,
} from "@fluentui/react-icons";

interface ScheduleItemProps {
  item: ScheduleItem;
  items: ScheduleItem[];
  index: number;
  selected?: boolean;
  onSelect?: () => void;
  onOpenChat?: () => void;
  onUpdate?: (
    id: string,
    updates: { start?: string; end?: string; title?: string; note?: string }
  ) => Promise<void>;
  onDuplicate?: () => void;
  onDelete?: () => void;
}

export function ScheduleItemComponent({
  item,
  items,
  index,
  selected = false,
  onSelect,
  onOpenChat,
  onUpdate,
  onDuplicate,
  onDelete,
}: ScheduleItemProps) {
  const [showOverflow, setShowOverflow] = useState(false);
  const overflowTriggerRef = useRef<HTMLButtonElement>(null);

  const isPastEvent = isPast(item.end);
  const hasConflict = hasOverlap(item, items, index);
  const accentColor = getAccentColor(item);

  const handleClick = (e: React.MouseEvent) => {
    if (e.shiftKey) {
      // Shift+Click opens full chat
      e.stopPropagation();
      onOpenChat?.();
      return;
    }
    // Regular click toggles selection
    onSelect?.();
  };

  const handleUpdate = async (
    id: string,
    updates: { start?: string; end?: string; title?: string; note?: string }
  ) => {
    if (!onUpdate) return;
    await onUpdate(id, updates);
  };

  return (
    <div
      className={`group relative z-0 hover:z-10 rounded-xl border ${
        hasConflict
          ? "border-amber-300 bg-amber-50/30"
          : "border-slate-200 bg-slate-50"
      } hover:bg-slate-100 transition ${
        selected ? "ring-2 ring-blue-500 ring-offset-2" : ""
      } ${isPastEvent ? "opacity-60 grayscale" : ""} ${accentColor}`}
      onClick={handleClick}
      tabIndex={0}
      role="button"
      aria-label={`${item.title}, ${formatTimeRange(item.start, item.end)}`}
      aria-expanded={selected}
    >
      {/* Hover hint indicator */}
      {!selected && onOpenChat && (
        <div
          className="pointer-events-none absolute left-4 md:left-5 bottom-3 hidden text-sky-700/70 group-hover:block text-xs select-none"
          aria-hidden="true"
        >
          Open full chat ↩︎
        </div>
      )}

      <div className="p-3 flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="px-4 md:px-5">
            <div className="truncate font-medium text-sm text-slate-900">
              {item.title}
            </div>
            <div className="text-xs text-slate-500 whitespace-nowrap mt-1">
              {formatTimeRange(item.start, item.end)}
            </div>
            {item.type === "block" && item.tasks && item.tasks.length > 0 && (
              <div className="text-xs text-slate-500 mt-1 truncate">
                {item.tasks.join(", ")}
              </div>
            )}
            {hasConflict && (
              <div className="mt-1 inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium text-amber-700 bg-amber-50">
                Conflict
              </div>
            )}

            {/* Smart Command Input */}
            {selected && onUpdate && (
              <SmartCommandInput
                itemId={item.id}
                start={item.start}
                end={item.end}
                onUpdate={handleUpdate}
                onOpenChat={() => {
                  onOpenChat?.();
                }}
                onClose={() => {
                  // Deselect when closing (toggle will deselect)
                  if (selected) {
                    onSelect?.();
                  }
                }}
              />
            )}
          </div>
        </div>

        {/* Actions: show vertical icons when expanded, overflow menu when collapsed */}
        {selected ? (
          // Expanded: show vertical icons for duplicate and delete
          <div className="flex flex-col gap-1">
            {onDuplicate && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDuplicate();
                }}
                className="inline-flex h-8 w-8 items-center justify-center rounded-md text-slate-700 hover:text-slate-900 hover:bg-slate-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 transition"
                aria-label="Duplicate"
              >
                <Copy24Regular className="h-5 w-5" />
              </button>
            )}
            {onDelete && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete();
                }}
                className="inline-flex h-8 w-8 items-center justify-center rounded-md text-slate-700 hover:text-red-600 hover:bg-red-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 transition-colors"
                aria-label="Delete"
              >
                <Delete24Regular className="h-5 w-5" />
              </button>
            )}
          </div>
        ) : (
          // Collapsed: show overflow menu button
          (onDuplicate || onDelete) && (
            <>
              <button
                ref={overflowTriggerRef}
                onClick={(e) => {
                  e.stopPropagation();
                  setShowOverflow(!showOverflow);
                }}
                className="inline-flex h-8 w-8 items-center justify-center rounded-md text-slate-700 hover:text-slate-900 hover:bg-slate-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 transition"
                aria-label="More options"
                aria-expanded={showOverflow}
                aria-haspopup="menu"
              >
                <MoreHorizontal24Regular className="h-5 w-5" />
              </button>
              <OverflowMenu
                open={showOverflow}
                onClose={() => setShowOverflow(false)}
                triggerRef={overflowTriggerRef as React.RefObject<HTMLElement>}
              >
                {onDuplicate && (
                  <OverflowMenuItem
                    onClick={(e) => {
                      e.stopPropagation();
                      onDuplicate();
                      setShowOverflow(false);
                    }}
                  >
                    Duplicate
                  </OverflowMenuItem>
                )}
                {onDelete && (
                  <OverflowMenuItem
                    variant="danger"
                    onClick={(e) => {
                      e.stopPropagation();
                      onDelete();
                      setShowOverflow(false);
                    }}
                  >
                    Delete
                  </OverflowMenuItem>
                )}
              </OverflowMenu>
            </>
          )
        )}
      </div>
    </div>
  );
}

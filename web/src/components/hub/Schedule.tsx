import { useState, useEffect, useCallback, useRef } from "react";
import { ScheduleItemComponent } from "./ScheduleItem";
import {
  segmentByPeriod,
  formatTime,
  type ScheduleItem,
  type PeriodGroup,
} from "../../lib/schedule";

interface ScheduleProps {
  events: ScheduleItem[];
  blocks: ScheduleItem[];
  onEditInChat?: (blockId: string) => void;
  onUpdateEvent?: (id: string, updates: { start?: string; end?: string; title?: string; note?: string }) => Promise<void>;
  onDuplicateEvent?: (id: string) => Promise<void>;
  onDeleteEvent?: (id: string) => Promise<void>;
}

export function Schedule({
  events,
  blocks,
  onEditInChat,
  onUpdateEvent,
  onDuplicateEvent,
  onDeleteEvent,
}: ScheduleProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [nowTime, setNowTime] = useState(new Date());
  const containerRef = useRef<HTMLDivElement>(null);

  // Combine and sort all items
  const allItems: ScheduleItem[] = [
    ...events.map((e) => ({ ...e, type: "event" as const })),
    ...blocks.map((b) => ({
      ...b,
      type: "block" as const,
      title: b.title || `${b.kind || "work"} block`,
    })),
  ].sort((a, b) => new Date(a.start).getTime() - new Date(b.start).getTime());

  // Group by period
  const groups = segmentByPeriod(allItems);

  // Update "Now" marker every minute
  useEffect(() => {
    const interval = setInterval(() => {
      setNowTime(new Date());
    }, 60000); // Update every minute
    return () => clearInterval(interval);
  }, []);

  // Find the index of the selected item
  const selectedIndex = allItems.findIndex((item) => item.id === selectedId);

  // Keyboard navigation
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      // Keyboard shortcuts work even when input is focused
      if (e.key === "[" || e.key === "]" || e.key === "-" || e.key === "=") {
        // These shortcuts work everywhere
        if (selectedId && onUpdateEvent) {
          e.preventDefault();
          const item = allItems[selectedIndex];
          if (!item) return;
          
          if (e.key === "[") {
            const newStart = new Date(item.start);
            newStart.setMinutes(newStart.getMinutes() - 15);
            const duration =
              new Date(item.end).getTime() - new Date(item.start).getTime();
            const newEnd = new Date(newStart.getTime() + duration).toISOString();
            onUpdateEvent(item.id, { start: newStart.toISOString(), end: newEnd });
          } else if (e.key === "]") {
            const newStart = new Date(item.start);
            newStart.setMinutes(newStart.getMinutes() + 15);
            const duration =
              new Date(item.end).getTime() - new Date(item.start).getTime();
            const newEnd = new Date(newStart.getTime() + duration).toISOString();
            onUpdateEvent(item.id, { start: newStart.toISOString(), end: newEnd });
          } else if (e.key === "-") {
            const newEnd = new Date(item.end);
            newEnd.setMinutes(newEnd.getMinutes() - 15);
            onUpdateEvent(item.id, { start: item.start, end: newEnd.toISOString() });
          } else if (e.key === "=") {
            const newEnd = new Date(item.end);
            newEnd.setMinutes(newEnd.getMinutes() + 15);
            onUpdateEvent(item.id, { start: item.start, end: newEnd.toISOString() });
          }
        }
        return;
      }
      
      // Don't interfere with text input for other keys
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return;
      }

      switch (e.key) {
        case "ArrowUp":
          e.preventDefault();
          if (selectedIndex > 0) {
            setSelectedId(allItems[selectedIndex - 1].id);
          }
          break;
        case "ArrowDown":
          e.preventDefault();
          if (selectedIndex < allItems.length - 1) {
            setSelectedId(allItems[selectedIndex + 1].id);
          }
          break;
        case "Enter":
          e.preventDefault();
          if (selectedId && onEditInChat) {
            onEditInChat(selectedId);
          }
          break;
        case "Escape":
          e.preventDefault();
          setSelectedId(null);
          break;
      }
    },
    [selectedId, selectedIndex, allItems, onEditInChat, onUpdateEvent]
  );

  useEffect(() => {
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);

  // Calculate if "Now" marker should be shown and its position
  const shouldShowNowMarker = () => {
    const now = nowTime.getTime();
    const todayStart = new Date(nowTime);
    todayStart.setHours(0, 0, 0, 0);
    const todayEnd = new Date(nowTime);
    todayEnd.setHours(23, 59, 59, 999);
    return now >= todayStart.getTime() && now <= todayEnd.getTime();
  };

  const getNowMarkerPosition = () => {
    if (allItems.length === 0) return null;
    const now = nowTime.getTime();
    // Find the first item that starts after now
    const afterIndex = allItems.findIndex(
      (item) => new Date(item.start).getTime() > now
    );
    return afterIndex === -1 ? allItems.length : afterIndex;
  };

  const renderGroup = (group: PeriodGroup, groupIndex: number) => {
    const nowPosition = getNowMarkerPosition();
    const itemsInGroup: ScheduleItem[] = [];
    let nowInserted = false;

    // Insert "Now" marker if needed
    if (shouldShowNowMarker() && nowPosition !== null) {
      let countBeforeGroup = 0;
      for (let i = 0; i < groupIndex; i++) {
        countBeforeGroup += groups[i].items.length;
      }

      for (let i = 0; i < group.items.length; i++) {
        const globalIndex = countBeforeGroup + i;
        if (globalIndex === nowPosition && !nowInserted) {
          itemsInGroup.push(null as any); // Marker placeholder
          nowInserted = true;
        }
        itemsInGroup.push(group.items[i]);
      }

      // If now marker should be at the end of this group
      if (
        !nowInserted &&
        countBeforeGroup + group.items.length === nowPosition
      ) {
        itemsInGroup.push(null as any); // Marker placeholder
      }
    } else {
      itemsInGroup.push(...group.items);
    }

    return (
      <div key={group.period} className="space-y-2">
        <div className="sticky top-0 bg-white/95 backdrop-blur-sm z-10 py-2 border-b border-slate-200">
          <h3 className="text-sm font-semibold text-slate-700">
            {group.label}
          </h3>
        </div>
        <div className="space-y-2">
          {itemsInGroup.map((item, idx) => {
            // Render "Now" marker
            if (!item) {
              return (
                <div
                  key="now-marker"
                  className="sticky top-12 z-10 flex items-center gap-2 py-1"
                >
                  <div className="flex-1 border-t-2 border-sky-400"></div>
                  <div className="px-2 py-0.5 bg-sky-50 border border-sky-200 rounded text-xs font-medium text-sky-700 whitespace-nowrap">
                    Now • {formatTime(nowTime.toISOString())}
                  </div>
                  <div className="flex-1 border-t-2 border-sky-400"></div>
                </div>
              );
            }

            const globalIndex = allItems.findIndex((i) => i.id === item.id);
            return (
              <ScheduleItemComponent
                key={item.id}
                item={item}
                items={allItems}
                index={globalIndex}
                selected={selectedId === item.id}
                onSelect={() => {
                  // Toggle selection: if already selected, deselect; otherwise select this one
                  setSelectedId(selectedId === item.id ? null : item.id);
                }}
                onOpenChat={
                  item.type === "block" && onEditInChat
                    ? () => onEditInChat(item.id)
                    : undefined
                }
                onUpdate={onUpdateEvent}
                onDuplicate={
                  onDuplicateEvent
                    ? () => onDuplicateEvent(item.id)
                    : undefined
                }
                onDelete={
                  onDeleteEvent ? () => onDeleteEvent(item.id) : undefined
                }
              />
            );
          })}
        </div>
      </div>
    );
  };

  return (
    <div ref={containerRef} className="space-y-4" tabIndex={0}>
      {groups.length === 0 ? (
        <div className="text-sm text-slate-500 py-4">
          No events or blocks scheduled
        </div>
      ) : (
        <div className="space-y-4">
          {groups.map((group, idx) => renderGroup(group, idx))}
        </div>
      )}
    </div>
  );
}


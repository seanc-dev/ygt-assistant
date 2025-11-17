import {
  useState,
  useCallback,
  useMemo,
  useEffect,
  useRef,
  createRef,
} from "react";
import { Panel, Stack, Text, Heading } from "@ygt-assistant/ui";
import { Button } from "@ygt-assistant/ui/primitives/Button";
import { useQueue, useSettings } from "../../hooks/useHubData";
import { ActionCard } from "./ActionCard";
import { QueueSection } from "./QueueSection";
import { api } from "../../lib/api";

interface ActionItem {
  action_id: string;
  source: "email" | "teams" | "doc";
  category: "needs_response" | "needs_approval" | "fyi";
  priority: "low" | "medium" | "high";
  preview: string;
  thread_id?: string;
  defer_until?: string;
  defer_bucket?: string;
  added_to_today?: boolean;
}

interface QueueResponse {
  ok: boolean;
  items: ActionItem[];
  total: number;
  limit: number;
  offset: number;
}

const VISIBLE_LIMIT = 5;
const PRELOAD_COUNT = 10;
const GRID_COLS_DESKTOP = 2;
const GRID_COLS_MOBILE = 1;

// Map category to action_label
function getActionLabel(
  category: ActionItem["category"]
): "Respond" | "Approve" | "Review" {
  switch (category) {
    case "needs_response":
      return "Respond";
    case "needs_approval":
      return "Approve";
    case "fyi":
      return "Review";
    default:
      return "Review";
  }
}

// Group items by priority
function groupByPriority(items: ActionItem[]): {
  high: ActionItem[];
  medium: ActionItem[];
  low: ActionItem[];
} {
  const groups = {
    high: [] as ActionItem[],
    medium: [] as ActionItem[],
    low: [] as ActionItem[],
  };
  items.forEach((item) => {
    groups[item.priority].push(item);
  });
  return groups;
}

export function ActionQueue() {
  const { data: queueData, mutate } = useQueue({ pollMs: 30000 });
  const { data: settings } = useSettings();
  const trustMode = (settings?.trust_level === "standard" ? "supervised" : settings?.trust_level) || "training_wheels";
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [visibleCount, setVisibleCount] = useState(VISIBLE_LIMIT);
  const [openMenuFor, setOpenMenuFor] = useState<string | null>(null);
  const [menuType, setMenuType] = useState<
    "defer" | "schedule" | "add-to-today" | null
  >(null);
  const cardRefs = useRef<Map<string, React.RefObject<HTMLDivElement | null>>>(
    new Map()
  );

  const queue = queueData as QueueResponse | undefined;
  const visibleItems = useMemo(() => {
    return queue?.items.slice(0, visibleCount) || [];
  }, [queue?.items, visibleCount]);
  const hasMore = queue && queue.total > visibleCount;

  // Group visible items by priority
  const groupedItems = useMemo(
    () => groupByPriority(visibleItems),
    [visibleItems]
  );

  // Flatten items for keyboard navigation (maintains priority order)
  const flatItems = useMemo(() => {
    return [...groupedItems.high, ...groupedItems.medium, ...groupedItems.low];
  }, [groupedItems]);

  // Get or create ref for a card
  const getCardRef = useCallback(
    (id: string): React.RefObject<HTMLDivElement | null> => {
      if (!cardRefs.current.has(id)) {
        const ref = createRef<HTMLDivElement>();
        cardRefs.current.set(id, ref);
      }
      return cardRefs.current.get(id)!;
    },
    []
  );

  // Get grid columns based on viewport
  const getGridCols = useCallback(() => {
    if (typeof window === "undefined") return GRID_COLS_DESKTOP;
    return window.innerWidth >= 1024 ? GRID_COLS_DESKTOP : GRID_COLS_MOBILE;
  }, []);

  // Navigate to next/previous item
  const navigateToItem = useCallback(
    (direction: "next" | "prev" | "up" | "down" | "right" | "left") => {
      if (flatItems.length === 0) return;

      const cols = getGridCols();
      let currentIndex = selectedId
        ? flatItems.findIndex((item) => item.action_id === selectedId)
        : -1;

      if (currentIndex === -1) {
        // No selection, start at first item
        setSelectedId(flatItems[0].action_id);
        return;
      }

      let nextIndex = currentIndex;

      if (direction === "next" || direction === "right") {
        nextIndex = Math.min(currentIndex + 1, flatItems.length - 1);
      } else if (direction === "prev" || direction === "left") {
        nextIndex = Math.max(currentIndex - 1, 0);
      } else if (direction === "down") {
        // Move down by row (add cols)
        nextIndex = Math.min(currentIndex + cols, flatItems.length - 1);
      } else if (direction === "up") {
        // Move up by row (subtract cols)
        nextIndex = Math.max(currentIndex - cols, 0);
      }

      const nextItem = flatItems[nextIndex];
      if (nextItem) {
        setSelectedId(nextItem.action_id);
        // Scroll into view
        const ref = getCardRef(nextItem.action_id);
        if (ref.current) {
          ref.current.scrollIntoView({ behavior: "smooth", block: "nearest" });
        }
      }
    },
    [flatItems, selectedId, getCardRef, getGridCols]
  );

  // Define handlers before useEffect
  const handleAddToToday = useCallback(
    async (actionId: string) => {
      try {
        // Default to "work" kind - can be extended later if needed
        await api.addToToday?.(actionId, { kind: "work" });
        mutate(); // Refresh queue
        setOpenMenuFor(null);
        setMenuType(null);
      } catch (err) {
        console.error("Failed to add to today:", err);
      }
    },
    [mutate]
  );

  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore if typing in input/textarea
      const target = e.target as HTMLElement;
      if (
        target.tagName === "INPUT" ||
        target.tagName === "TEXTAREA" ||
        target.isContentEditable
      ) {
        return;
      }

      // Prevent default for navigation keys
      if (
        [
          "ArrowUp",
          "ArrowDown",
          "ArrowLeft",
          "ArrowRight",
          "Enter",
          "Escape",
        ].includes(e.key)
      ) {
        e.preventDefault();
      }

      switch (e.key) {
        case "ArrowRight":
          navigateToItem("right");
          break;
        case "ArrowLeft":
          navigateToItem("left");
          break;
        case "ArrowDown":
          navigateToItem("down");
          break;
        case "ArrowUp":
          navigateToItem("up");
          break;
        case "Enter":
          if (selectedId) {
            setExpandedId(selectedId);
          }
          break;
        case "Escape":
          if (expandedId) {
            setExpandedId(null);
            // Return focus to card
            if (expandedId) {
              const ref = getCardRef(expandedId);
              if (ref.current) {
                ref.current.focus();
              }
            }
          } else if (selectedId) {
            setSelectedId(null);
          }
          break;
        case "d":
        case "D":
          if (selectedId && !openMenuFor) {
            setOpenMenuFor(selectedId);
            setMenuType("defer");
          }
          break;
        case "s":
        case "S":
          if (selectedId && !openMenuFor) {
            setOpenMenuFor(selectedId);
            setMenuType("schedule");
          }
          break;
        case "t":
        case "T":
          if (selectedId && !openMenuFor) {
            handleAddToToday(selectedId);
          }
          break;
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [
    selectedId,
    expandedId,
    navigateToItem,
    openMenuFor,
    getCardRef,
    handleAddToToday,
  ]);

  const handleToggleExpand = useCallback((id: string) => {
    setExpandedId((prev) => (prev === id ? null : id));
    setSelectedId(id);
    // Close any open menus
    setOpenMenuFor(null);
    setMenuType(null);
  }, []);

  const handleCardClick = useCallback(
    (id: string) => {
      setSelectedId(id);
      handleToggleExpand(id);
    },
    [handleToggleExpand]
  );

  const handleDefer = useCallback(
    async (
      actionId: string,
      bucket: "afternoon" | "tomorrow" | "this_week" | "next_week"
    ) => {
      try {
        await api.deferAction?.(actionId, { bucket });
        mutate(); // Refresh queue
        setOpenMenuFor(null);
        setMenuType(null);
      } catch (err) {
        console.error("Failed to defer:", err);
      }
    },
    [mutate]
  );

  const handleCreateTask = useCallback(
    async (actionId: string) => {
      try {
        // TODO: Create task endpoint doesn't exist yet - stub for now
        const item = queue?.items.find((i) => i.action_id === actionId);
        if (!item) return;

        console.log("Create task for action:", actionId, item.preview);
        // TODO: Implement when task creation endpoint is available

        alert(`Task creation queued for: ${item.preview.substring(0, 50)}...`);
        mutate(); // Refresh queue
        setOpenMenuFor(null);
        setMenuType(null);
      } catch (err) {
        console.error("Failed to create task:", err);
        alert("Failed to create task. Please try again.");
      }
    },
    [queue?.items, mutate]
  );

  const handleSchedule = useCallback(
    async (
      actionId: string,
      bucket: "afternoon" | "tomorrow" | "this_week" | "next_week"
    ) => {
      try {
        // TODO: Hook into real schedule endpoint when available
        console.log("Schedule action:", actionId, bucket);
        mutate(); // Refresh queue
        setOpenMenuFor(null);
        setMenuType(null);
      } catch (err) {
        console.error("Failed to schedule:", err);
      }
    },
    [mutate]
  );

  const handleOpenSchedule = useCallback((actionId: string) => {
    setOpenMenuFor(actionId);
    setMenuType("schedule");
  }, []);

  const handleShowMore = useCallback(() => {
    setVisibleCount((prev) =>
      Math.min(prev + VISIBLE_LIMIT, queue?.total || prev)
    );
  }, [queue?.total]);

  return (
    <Panel>
      <Stack gap="md">
        <div className="flex justify-between items-center">
          <Heading as="h2" variant="title">
            Action Queue
          </Heading>
          {queue && (
            <Text variant="caption" className="text-sm text-slate-600">
              {queue.total} total
            </Text>
          )}
        </div>

        {!queue ? (
          <Text variant="muted">Loading queue...</Text>
        ) : visibleItems.length === 0 ? (
          <div className="text-center py-8">
            <Text variant="body" className="text-lg">
              All clear for now. 👏
            </Text>
          </div>
        ) : (
          <>
            {/* High Priority Section */}
            {groupedItems.high.length > 0 && (
              <QueueSection
                title="High priority"
                count={groupedItems.high.length}
              >
                <div
                  className="grid grid-cols-1 lg:grid-cols-2 auto-rows-auto items-start gap-6"
                  role="listbox"
                  aria-label="High priority action items"
                >
                  {groupedItems.high.map((item) => (
                    <ActionCard
                      key={item.action_id}
                      item={{
                        ...item,
                        action_label: getActionLabel(item.category),
                      }}
                      expanded={expandedId === item.action_id}
                      selected={selectedId === item.action_id}
                      onToggleExpand={handleCardClick}
                      onDefer={handleDefer}
                      onAddToToday={handleAddToToday}
                      onCreateTask={handleCreateTask}
                      onSchedule={handleSchedule}
                      onOpenSchedule={handleOpenSchedule}
                      cardRef={getCardRef(item.action_id)}
                      trustMode={trustMode}
                    />
                  ))}
                </div>
              </QueueSection>
            )}

            {/* Medium Priority Section */}
            {groupedItems.medium.length > 0 && (
              <QueueSection title="Medium" count={groupedItems.medium.length}>
                <div
                  className="grid grid-cols-1 lg:grid-cols-2 auto-rows-auto items-start gap-6"
                  role="listbox"
                  aria-label="Medium priority action items"
                >
                  {groupedItems.medium.map((item) => (
                    <ActionCard
                      key={item.action_id}
                      item={{
                        ...item,
                        action_label: getActionLabel(item.category),
                      }}
                      expanded={expandedId === item.action_id}
                      selected={selectedId === item.action_id}
                      onToggleExpand={handleCardClick}
                      onDefer={handleDefer}
                      onAddToToday={handleAddToToday}
                      onCreateTask={handleCreateTask}
                      onSchedule={handleSchedule}
                      onOpenSchedule={handleOpenSchedule}
                      cardRef={getCardRef(item.action_id)}
                      trustMode={trustMode}
                    />
                  ))}
                </div>
              </QueueSection>
            )}

            {/* Low Priority Section */}
            {groupedItems.low.length > 0 && (
              <QueueSection title="Low" count={groupedItems.low.length}>
                <div
                  className="grid grid-cols-1 lg:grid-cols-2 auto-rows-auto items-start gap-6"
                  role="listbox"
                  aria-label="Low priority action items"
                >
                  {groupedItems.low.map((item) => (
                    <ActionCard
                      key={item.action_id}
                      item={{
                        ...item,
                        action_label: getActionLabel(item.category),
                      }}
                      expanded={expandedId === item.action_id}
                      selected={selectedId === item.action_id}
                      onToggleExpand={handleCardClick}
                      onDefer={handleDefer}
                      onAddToToday={handleAddToToday}
                      onCreateTask={handleCreateTask}
                      onSchedule={handleSchedule}
                      onOpenSchedule={handleOpenSchedule}
                      cardRef={getCardRef(item.action_id)}
                      trustMode={trustMode}
                    />
                  ))}
                </div>
              </QueueSection>
            )}

            {hasMore && (
              <div className="flex justify-center pt-6">
                <Button onClick={handleShowMore} variant="outline">
                  Show more ({queue.total - visibleCount} remaining)
                </Button>
              </div>
            )}
          </>
        )}
      </Stack>
    </Panel>
  );
}

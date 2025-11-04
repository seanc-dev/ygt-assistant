import { useState, useCallback, useMemo } from "react";
import { Panel, Stack, Text, Button, Heading } from "@ygt-assistant/ui";
import { useQueue } from "../../hooks/useHubData";
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
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [visibleCount, setVisibleCount] = useState(VISIBLE_LIMIT);

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

  const handleToggleExpand = useCallback((id: string) => {
    setExpandedId((prev) => (prev === id ? null : id));
  }, []);

  const handleDefer = useCallback(
    async (
      actionId: string,
      bucket: "afternoon" | "tomorrow" | "this_week" | "next_week"
    ) => {
      try {
        await api.deferAction?.(actionId, { bucket });
        mutate(); // Refresh queue
      } catch (err) {
        console.error("Failed to defer:", err);
      }
    },
    [mutate]
  );

  const handleAddToToday = useCallback(
    async (actionId: string) => {
      try {
        // Default to "work" kind - can be extended later if needed
        await api.addToToday?.(actionId, { kind: "work" });
        mutate(); // Refresh queue
      } catch (err) {
        console.error("Failed to add to today:", err);
      }
    },
    [mutate]
  );

  const handleChat = useCallback((actionId: string) => {
    // Expand the card to show chat
    setExpandedId((prev) => (prev === actionId ? null : actionId));
  }, []);

  const handleCreateTask = useCallback(
    async (actionId: string) => {
      try {
        // TODO: Create task endpoint doesn't exist yet - stub for now
        // When available, should create a task first, then optionally create a thread
        const item = queue?.items.find((i) => i.action_id === actionId);
        if (!item) return;

        // For now, just log and show a user-friendly message
        console.log("Create task for action:", actionId, item.preview);
        // TODO: Implement when task creation endpoint is available
        // await api.createTask?.({ source_action_id: actionId, title: item.preview, priority: item.priority });

        // Show success message (could use toast notification)
        alert(`Task creation queued for: ${item.preview.substring(0, 50)}...`);
        mutate(); // Refresh queue
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
      preset: "focus_30m" | "focus_60m" | "block_pm_admin" | "pick_time"
    ) => {
      try {
        // TODO: Hook into real schedule endpoint when available
        // await api.scheduleAction?.(actionId, { preset });
        console.log("Schedule action:", actionId, preset);
        mutate(); // Refresh queue
      } catch (err) {
        console.error("Failed to schedule:", err);
      }
    },
    [mutate]
  );

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
                  role="list"
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
                      onToggleExpand={handleToggleExpand}
                      onDefer={handleDefer}
                      onAddToToday={handleAddToToday}
                      onOpenChat={handleChat}
                      onCreateTask={handleCreateTask}
                      onSchedule={handleSchedule}
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
                  role="list"
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
                      onToggleExpand={handleToggleExpand}
                      onDefer={handleDefer}
                      onAddToToday={handleAddToToday}
                      onOpenChat={handleChat}
                      onCreateTask={handleCreateTask}
                      onSchedule={handleSchedule}
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
                  role="list"
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
                      onToggleExpand={handleToggleExpand}
                      onDefer={handleDefer}
                      onAddToToday={handleAddToToday}
                      onOpenChat={handleChat}
                      onCreateTask={handleCreateTask}
                      onSchedule={handleSchedule}
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

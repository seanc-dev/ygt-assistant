import { useState, useCallback } from "react";
import { Panel, Stack, Text, Button, Heading } from "@ygt-assistant/ui";
import { useQueue } from "../../hooks/useHubData";
import { InlineExpandableCard } from "../InlineExpandableCard";
import { DeferMenu } from "../DeferMenu";
import { AddToTodayButton } from "../AddToTodayButton";
import { CompactChat } from "../CompactChat";
import { api } from "../../lib/api";
import { useRouter } from "next/router";

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

export function ActionQueue() {
  const router = useRouter();
  const { data: queueData, mutate } = useQueue({ pollMs: 30000 });
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [visibleCount, setVisibleCount] = useState(VISIBLE_LIMIT);

  const queue = queueData as QueueResponse | undefined;
  const visibleItems = queue?.items.slice(0, visibleCount) || [];
  const hasMore = queue && queue.total > visibleCount;

  const handleDefer = useCallback(
    async (actionId: string, bucket: string) => {
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
    async (actionId: string, kind: "admin" | "work") => {
      try {
        await api.addToToday?.(actionId, { kind });
        mutate(); // Refresh queue
      } catch (err) {
        console.error("Failed to add to today:", err);
      }
    },
    [mutate]
  );

  const handleLoadMore = useCallback(() => {
    setVisibleCount((prev) => Math.min(prev + VISIBLE_LIMIT, queue?.total || prev));
  }, [queue?.total]);

  const handleChat = useCallback((actionId: string, threadId?: string) => {
    // Expand the card to show chat
    setExpandedId(expandedId === actionId ? null : actionId);
  }, [expandedId]);

  const handleOpenInWorkroom = useCallback(() => {
    router.push("/workroom");
  }, [router]);

  return (
    <Panel>
      <Stack gap="md">
        <div className="flex justify-between items-center">
          <Heading as="h2" variant="title">
            Action Queue
          </Heading>
          {queue && (
            <Text variant="caption" className="text-sm text-gray-600">
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
            <div className="grid gap-4 grid-cols-1 md:grid-cols-2 lg:grid-cols-3" role="list" aria-label="Action items queue">
              {visibleItems.map((item, index) => (
                <InlineExpandableCard
                  key={item.action_id}
                  expanded={expandedId === item.action_id}
                  onToggle={() => setExpandedId(expandedId === item.action_id ? null : item.action_id)}
                  preview={
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <Text variant="label" className="text-sm font-medium" aria-label={`Source: ${item.source}`}>
                          {item.source.toUpperCase()}
                        </Text>
                        <Text
                          variant="caption"
                          className={`text-xs px-2 py-1 rounded ${
                            item.priority === "high"
                              ? "bg-red-100 text-red-800"
                              : item.priority === "medium"
                              ? "bg-yellow-100 text-yellow-800"
                              : "bg-gray-100 text-gray-800"
                          }`}
                          aria-label={`Priority: ${item.priority}`}
                        >
                          {item.priority}
                        </Text>
                      </div>
                      <Text variant="body" className="text-sm">
                        {item.preview.substring(0, 100)}
                        {item.preview.length > 100 ? "..." : ""}
                      </Text>
                      <Text variant="caption" className="text-xs mt-1">
                        {item.category.replace("_", " ")}
                      </Text>
                    </div>
                  }
                  role="listitem"
                  aria-posinset={index + 1}
                  aria-setsize={visibleItems.length}
                >
                  <div className="space-y-3">
                    <Text variant="body" className="text-sm">
                      {item.preview}
                    </Text>
                    <div className="flex gap-2 flex-wrap">
                      <DeferMenu onDefer={(bucket) => handleDefer(item.action_id, bucket)} />
                      <AddToTodayButton
                        onAddToToday={(kind) => handleAddToToday(item.action_id, kind)}
                      />
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleChat(item.action_id, item.thread_id)}
                      >
                        Chat
                      </Button>
                    </div>
                    {expandedId === item.action_id && (
                      <CompactChat
                        threadId={item.thread_id}
                        onOpenInWorkroom={handleOpenInWorkroom}
                      />
                    )}
                  </div>
                </InlineExpandableCard>
              ))}
            </div>

            {hasMore && (
              <div className="flex justify-center pt-4">
                <Button onClick={handleLoadMore} variant="secondary">
                  Load more ({queue.total - visibleCount} remaining)
                </Button>
              </div>
            )}
          </>
        )}
      </Stack>
    </Panel>
  );
}


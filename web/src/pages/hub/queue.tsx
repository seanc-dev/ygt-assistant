import { useEffect, useState, useCallback } from "react";
import { Heading, Panel, Stack, Text, Button } from "@ygt-assistant/ui";
import { Layout } from "../../components/Layout";
import { api } from "../../lib/api";
import { InlineExpandableCard } from "../../components/InlineExpandableCard";
import { DeferMenu } from "../../components/DeferMenu";
import { AddToTodayButton } from "../../components/AddToTodayButton";
import { CompactChat } from "../../components/CompactChat";
import { useHotkeys } from "../../hooks/useHotkeys";
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

export default function QueuePage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [queue, setQueue] = useState<QueueResponse | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [offset, setOffset] = useState(0);
  const [settings, setSettings] = useState<any>(null);
  const VISIBLE_LIMIT = 5;
  const PRELOAD_COUNT = 10;

  // Load settings for hotkeys
  useEffect(() => {
    api.settings().then((data) => setSettings(data)).catch(() => {});
  }, []);

  const loadQueue = useCallback(async (offset = 0) => {
    try {
      const data = await api.queue();
      setQueue(data as QueueResponse);
      setLoading(false);
    } catch (err) {
      console.error("Failed to load queue:", err);
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadQueue(0);
    // Poll every 30s for new items
    const interval = setInterval(() => {
      loadQueue(0);
    }, 30000);
    return () => clearInterval(interval);
  }, [loadQueue]);

  const handleDefer = useCallback(
    async (actionId: string, bucket: string) => {
      try {
        await api.deferAction?.(actionId, { bucket });
        await loadQueue(0);
      } catch (err) {
        console.error("Failed to defer:", err);
      }
    },
    [loadQueue]
  );

  const handleAddToToday = useCallback(
    async (actionId: string, kind: "admin" | "work") => {
      try {
        await api.addToToday?.(actionId, { kind });
        await loadQueue(0);
      } catch (err) {
        console.error("Failed to add to today:", err);
      }
    },
    [loadQueue]
  );

  const handleLoadMore = useCallback(() => {
    setOffset((prev) => prev + VISIBLE_LIMIT);
  }, []);

  const visibleItems = queue?.items.slice(0, VISIBLE_LIMIT) || [];
  const hasMore = queue && queue.total > offset + VISIBLE_LIMIT;
  const firstItem = visibleItems[0];

  // Hotkeys
  const hotkeyConfig = settings?.ui_prefs?.hotkeys || {};
  useHotkeys(
    {
      defer: () => firstItem && handleDefer(firstItem.action_id, "tomorrow"),
      add_to_today: () => firstItem && handleAddToToday(firstItem.action_id, "work"),
      collapse: () => setExpandedId(null),
      open_workroom: () => router.push("/workroom"),
      settings: () => router.push("/settings"),
    },
    hotkeyConfig,
    true
  );

  return (
    <Layout>
      <Stack gap="lg">
        <div className="flex flex-col gap-2">
          <Heading as="h1" variant="display">
            Queue
          </Heading>
          <Text variant="muted">
            Action items from Outlook, Teams, and Docs change summaries.{" "}
            {queue && `Total: ${queue.total}`}
          </Text>
        </div>

        <div className="grid gap-4 grid-cols-1 md:grid-cols-2 lg:grid-cols-3" role="list" aria-label="Action items queue">
          {loading && !queue ? (
            <Panel>
              <Text variant="muted">Loading queue...</Text>
            </Panel>
          ) : visibleItems.length === 0 ? (
            <Panel>
              <Text variant="muted">Queue is empty.</Text>
            </Panel>
          ) : (
            visibleItems.map((item, index) => (
              <InlineExpandableCard
                key={item.action_id}
                expanded={expandedId === item.action_id}
                onToggle={() =>
                  setExpandedId(
                    expandedId === item.action_id ? null : item.action_id
                  )
                }
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
                    <DeferMenu
                      onDefer={(bucket) => handleDefer(item.action_id, bucket)}
                    />
                    <AddToTodayButton
                      onAddToToday={(kind) =>
                        handleAddToToday(item.action_id, kind)
                      }
                    />
                    <Button
                      variant="secondary"
                      onClick={() => {
                        // TODO: Open inline chat
                      }}
                    >
                      Chat
                    </Button>
                  </div>
                  {expandedId === item.action_id && (
                    <CompactChat
                      threadId={item.thread_id}
                      onOpenInWorkroom={() => {
                        // TODO: Navigate to workroom
                      }}
                    />
                  )}
                </div>
              </InlineExpandableCard>
            ))
          )}
        </div>

        {hasMore && (
          <Panel>
            <Button onClick={handleLoadMore} variant="secondary">
              Load more ({queue.total - offset - VISIBLE_LIMIT} remaining)
            </Button>
          </Panel>
        )}
      </Stack>
    </Layout>
  );
}

import { useEffect, useMemo, useState } from "react";
import { Badge, Button, Heading, Panel, Stack, Text } from "@ygt-assistant/ui";
import { api } from "../../lib/api";
import { Layout } from "../../components/Layout";
import { Toast } from "../../components/Toast";

type Event = {
  ts: string;
  verb: string;
  object: string;
  id: string;
  summary?: string;
};

type Layer = "approvals" | "drafts" | "automations" | "system";

const layerLabels: Record<Layer, string> = {
  approvals: "Approvals",
  drafts: "Drafts",
  automations: "Automations",
  system: "System",
};

function resolveLayer(event: Event): Layer {
  if (event.object?.includes("draft")) return "drafts";
  if (event.object?.includes("automation")) return "automations";
  if (event.object?.includes("approval")) return "approvals";
  return "system";
}

type TimelineGroup = {
  layer: Layer;
  events: Event[];
};

export default function HistoryPage() {
  const [events, setEvents] = useState<Event[]>([]);
  const [filter, setFilter] = useState<Layer | "all">("all");
  const [toast, setToast] = useState("");

  useEffect(() => {
    api
      .history(100)
      .then((data) => setEvents(data || []))
      .catch(() => setEvents([]));
  }, []);

  const groups = useMemo(() => {
    const grouped = new Map<Layer, Event[]>();
    events.forEach((event) => {
      const layer = resolveLayer(event);
      if (!grouped.has(layer)) grouped.set(layer, []);
      grouped.get(layer)?.push(event);
    });
    return Array.from(grouped.entries())
      .map(([layer, layerEvents]) => ({ layer, events: layerEvents }))
      .sort((a, b) => a.layer.localeCompare(b.layer));
  }, [events]);

  const visibleGroups = groups.filter((group) => filter === "all" || group.layer === filter);

  const filteredCount = visibleGroups.reduce((total, group) => total + group.events.length, 0);

  const handleUndo = async (event: Event) => {
    if (event.object?.includes("approval")) {
      try {
        await api.undo(event.id);
        setToast("Undo requested");
      } catch {
        setToast("Unable to undo");
      }
    } else {
      setToast("Undo available from source view");
    }
  };

  const handleReplay = (event: Event) => {
    setToast(`Replay queued for ${event.object}`);
  };

  return (
    <Layout>
      <Stack gap="lg">
        <div className="flex flex-col gap-2">
          <Heading as="h1" variant="display">
            Memory timeline
          </Heading>
          <Text variant="muted">
            Browse actions grouped by layer. Jump back to their origin or replay the most useful flows.
          </Text>
        </div>

        <Panel tone="soft" kicker="Filter">
          <Stack direction="horizontal" gap="sm" wrap>
            <Button variant={filter === "all" ? "secondary" : "ghost"} onClick={() => setFilter("all")}>
              All
            </Button>
            {Object.entries(layerLabels).map(([layer, label]) => (
              <Button
                key={layer}
                variant={filter === layer ? "secondary" : "ghost"}
                onClick={() => setFilter(layer as Layer)}
              >
                {label}
              </Button>
            ))}
          </Stack>
        </Panel>

        <Panel
          kicker="Timeline"
          title="Recent activity"
          description={`Showing ${filteredCount} items`}
        >
          {filteredCount === 0 ? (
            <Text variant="muted">No entries match this layer yet.</Text>
          ) : (
            <Stack gap="lg">
              {visibleGroups.map((group) => (
                <div key={group.layer} className="space-y-4">
                  <div className="flex items-center justify-between">
                    <Text variant="label" className="text-[color:var(--ds-text-primary)]">
                      {layerLabels[group.layer]}
                    </Text>
                    <Badge tone="neutral">{group.events.length}</Badge>
                  </div>
                  <Stack gap="sm">
                    {group.events.map((event) => (
                      <div
                        key={`${group.layer}-${event.id}-${event.ts}`}
                        className="rounded-lg border border-[color:var(--ds-border-subtle)] bg-[color:var(--ds-surface)] p-4"
                      >
                        <Stack gap="sm">
                          <div className="flex items-center justify-between">
                            <Text variant="body">
                              {event.summary || `${event.verb} ${event.object}`}
                            </Text>
                            <Text variant="caption">
                              {new Date(event.ts).toLocaleString()}
                            </Text>
                          </div>
                          <Stack direction="horizontal" gap="sm" wrap>
                            <Button variant="ghost" onClick={() => handleUndo(event)}>
                              Undo
                            </Button>
                            <Button variant="ghost" onClick={() => handleReplay(event)}>
                              Replay
                            </Button>
                            <Button variant="secondary" onClick={() => setToast("Opening source")}>Open source</Button>
                          </Stack>
                        </Stack>
                      </div>
                    ))}
                  </Stack>
                </div>
              ))}
            </Stack>
          )}
        </Panel>
      </Stack>

      {toast ? <Toast message={toast} onClose={() => setToast("")} /> : null}
    </Layout>
  );
}

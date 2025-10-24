import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ActionBar,
  Badge,
  Button,
  Heading,
  Panel,
  Stack,
  Text,
} from "@ygt-assistant/ui";
import { useRouter } from "next/router";
import { api } from "../../lib/api";
import { Layout } from "../../components/Layout";
import { Toast } from "../../components/Toast";

type Approval = {
  id: string;
  kind?: string;
  title?: string;
  summary?: string;
  status?: string;
  metadata?: Record<string, string>;
};

const FILTERS = [
  { key: "all", label: "All" },
  { key: "email", label: "Email" },
  { key: "calendar", label: "Calendar" },
];

export default function ReviewPage() {
  const router = useRouter();
  const [filter, setFilter] = useState<string>("all");
  const [items, setItems] = useState<Approval[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [toast, setToast] = useState<string>("");

  const current = items[0];
  const queue = items.slice(1);

  const load = useCallback(
    async (nextFilter: string) => {
      setLoading(true);
      try {
        const res = await api.approvals(nextFilter);
        setItems(res || []);
      } finally {
        setLoading(false);
      }
    },
    []
  );

  useEffect(() => {
    load(filter);
  }, [filter, load]);

  const optimistic = useCallback((id: string, status: string) => {
    setItems((prev) => prev.map((a) => (a.id === id ? { ...a, status } : a)));
  }, []);

  const withUndoToast = useCallback((message: string) => {
    setToast(`${message}. Press U to undo`);
  }, []);

  const onApprove = useCallback(
    async (id: string) => {
      optimistic(id, "approved");
      withUndoToast("Approved");
      // Show irreversible warning for email sends when live
      setToast("Sending is irreversible. Hold to approve in live mode.");
      try {
        await api.approve(id);
      } catch {
        await load(filter);
      }
    },
    [filter, load, optimistic, withUndoToast]
  );

  const onEdit = useCallback(
    async (id: string) => {
      optimistic(id, "edited");
      setToast("Opened for edit");
      try {
        await api.edit(id, "tweak");
      } catch {
        await load(filter);
      }
    },
    [filter, load, optimistic]
  );

  const onSkip = useCallback(
    async (id: string) => {
      optimistic(id, "skipped");
      setToast("Snoozed");
      try {
        await api.skip(id);
      } catch {
        await load(filter);
      }
    },
    [filter, load, optimistic]
  );

  const onUndo = useCallback(
    async (id: string) => {
      optimistic(id, "proposed");
      setToast("Undo queued");
      try {
        await api.undo(id);
      } catch {
        await load(filter);
      }
    },
    [filter, load, optimistic]
  );

  const keyHandler = useCallback(
    (event: KeyboardEvent) => {
      const tag = (event.target as HTMLElement)?.tagName;
      if (["INPUT", "TEXTAREA"].includes(tag || "")) return;
      const first = items[0];
      if (!first) return;
      const key = event.key.toLowerCase();
      if (key === "a") onApprove(first.id);
      if (key === "e") onEdit(first.id);
      if (key === "s") onSkip(first.id);
      if (key === "u") onUndo(first.id);
    },
    [items, onApprove, onEdit, onSkip, onUndo]
  );

  useEffect(() => {
    window.addEventListener("keydown", keyHandler);
    return () => window.removeEventListener("keydown", keyHandler);
  }, [keyHandler]);

  const keyboardHints = useMemo(
    () => ["A approve", "E edit", "S skip", "U undo"],
    []
  );

  return (
    <Layout>
      <Stack gap="lg">
        <div className="flex flex-col gap-2">
          <Heading as="h1" variant="display">
            Focus review
          </Heading>
          <Text variant="muted">
            Work one decision at a time. Your queue stays nearby, and undo is only a keypress away.
          </Text>
        </div>

        <Panel tone="soft" kicker="View">
          <Stack direction="horizontal" gap="sm" wrap>
            {FILTERS.map((item) => (
              <Button
                key={item.key}
                variant={filter === item.key ? "secondary" : "ghost"}
                onClick={() => setFilter(item.key)}
                disabled={loading && filter === item.key}
              >
                {item.label}
              </Button>
            ))}
            <div className="flex-1" />
            <Button
              variant="ghost"
              onClick={async () => {
                await api.scan(["email", "calendar"]);
                await load(filter);
              }}
            >
              Rescan inbox
            </Button>
          </Stack>
        </Panel>

        <div className="grid gap-4 lg:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
          <Panel
            kicker={current ? current.kind || "Approval" : "Queue empty"}
            title={current ? current.title || current.summary || current.id : "Nothing to review"}
              description={
                current
                  ? "Respond with confidence. Secondary actions stay tucked away until you need them."
                  : "You’re clear for now. New proposals will land here first."
              }
            actions={
              current ? (
                <Badge tone="calm">Top priority</Badge>
              ) : (
                <Badge tone="neutral">Idle</Badge>
              )
            }
            footer={
              current ? (
                <Stack direction="horizontal" justify="between" align="center">
                  <Text variant="caption">Status: {current.status || "Proposed"}</Text>
                  <Button variant="ghost" onClick={() => onUndo(current.id)}>
                    Undo last change
                  </Button>
                </Stack>
              ) : null
            }
          >
            {loading && !current ? <Text variant="muted">Loading…</Text> : null}
            {current ? (
              <Stack gap="md">
                <div className="space-y-2 rounded-lg border border-[color:var(--ds-border-subtle)] bg-[color:var(--ds-surface)] p-4">
                  <Text variant="body">
                    {current.summary || "No summary available. Pull additional context if needed."}
                  </Text>
                  {current.metadata ? (
                    <dl className="grid gap-2 text-sm text-[color:var(--ds-text-secondary)] sm:grid-cols-2">
                      {Object.entries(current.metadata).map(([key, value]) => (
                        <div key={key}>
                          <dt className="font-medium capitalize">{key.replace(/_/g, " ")}</dt>
                          <dd>{value}</dd>
                        </div>
                      ))}
                    </dl>
                  ) : null}
                </div>
                <Stack direction="horizontal" gap="sm" wrap align="center">
                  <Button variant="secondary" onClick={() => onEdit(current.id)}>
                    Open for edits
                  </Button>
                  <Button variant="ghost" onClick={() => onSkip(current.id)}>
                    Skip for later
                  </Button>
                  <Button variant="ghost" onClick={() => router.push("/history")}>View history</Button>
                </Stack>
              </Stack>
            ) : (
              <Text variant="muted">
                Queue is empty. Relax or explore history while Microsoft Graph keeps listening.
              </Text>
            )}
          </Panel>

            <Panel
              kicker="Queue"
              title="Up next"
              description="Stay aware of what’s queued without breaking focus."
            footer={
              <Text variant="caption">
                Items automatically reshuffle as you approve. Undo brings them right back.
              </Text>
            }
          >
            {loading && items.length === 0 ? <Text variant="muted">Loading queue…</Text> : null}
            {queue.length === 0 ? (
              <Text variant="muted">No additional approvals waiting.</Text>
            ) : (
              <Stack gap="sm">
                {queue.map((item) => (
                  <div
                    key={item.id}
                    className="rounded-lg border border-[color:var(--ds-border-subtle)] bg-[color:var(--ds-surface-muted)] p-3"
                  >
                    <Text variant="label" className="text-[color:var(--ds-text-primary)]">
                      {item.title || item.summary || item.id}
                    </Text>
                    <div className="flex items-center justify-between text-xs text-[color:var(--ds-text-subtle)]">
                      <span>{item.kind || "proposal"}</span>
                      <span>{item.status || "pending"}</span>
                    </div>
                  </div>
                ))}
              </Stack>
            )}
          </Panel>
        </div>

          <ActionBar
            helperText={current ? "Approve the highlighted suggestion" : "You’re caught up"}
          primaryAction={
            <Button onClick={() => current && onApprove(current.id)} disabled={!current}>
              Approve and move forward
            </Button>
          }
          secondaryActions={keyboardHints.map((hint) => (
            <span key={hint}>{hint}</span>
          ))}
        />
      </Stack>

      {toast ? <Toast message={toast} onClose={() => setToast("")} /> : null}
    </Layout>
  );
}

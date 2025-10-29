import Link from "next/link";
import { useRouter } from "next/router";
import { useEffect, useState } from "react";
import {
  ActionBar,
  Badge,
  Button,
  Heading,
  Panel,
  Stack,
  Text,
} from "@ygt-assistant/ui";
import { api } from "../lib/api";
import { Layout } from "../components/Layout";

type Approval = {
  id: string;
  title?: string;
  summary?: string;
  due_at?: string;
};

type ConnectionStatus =
  | { state: "loading" }
  | {
      state: "connected";
      expires_at?: string;
      scopes?: string[];
      tenant_id?: string;
    }
  | { state: "disconnected"; reason?: string }
  | { state: "error"; message: string };

type FocusBlock = {
  label: string;
  time: string;
};

export default function Home() {
  const router = useRouter();
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [focusBlocks, setFocusBlocks] = useState<FocusBlock[]>([]);
  const [connection, setConnection] = useState<ConnectionStatus>({
    state: "loading",
  });

  useEffect(() => {
    api
      .approvals("all")
      .then((res) => setApprovals((res || []).slice(0, 4)))
      .catch(() => setApprovals([]));

    fetch(
      `${
        process.env.NEXT_PUBLIC_ADMIN_API_BASE ||
        "https://api.ygt-assistant.com"
      }/calendar/plan-today`,
      { credentials: "include" }
    )
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((data) =>
        setFocusBlocks(
          (data.plan || []).map((item: any) => ({
            time: item.time || "",
            label: item.title || item.summary || "Focus",
          }))
        )
      )
      .catch(() => setFocusBlocks([]));
  }, []);

  useEffect(() => {
    const apiBase =
      process.env.NEXT_PUBLIC_ADMIN_API_BASE || "http://localhost:8000";
    const userId = "local-user";

    setConnection({ state: "loading" });

    fetch(`${apiBase}/connections/ms/status`, { credentials: "include" })
      .then((res) => (res.ok ? res.json() : Promise.reject(res.statusText)))
      .then((data) => {
        if (data?.connected) {
          setConnection({ state: "connected", ...data });
        } else {
          setConnection({
            state: "disconnected",
            reason: data?.reason || "Needs Microsoft Graph connection",
          });
        }
      })
      .catch((error) =>
        setConnection({
          state: "error",
          message: typeof error === "string" ? error : "Unable to load status",
        })
      );
  }, []);

  const primaryAction = (
    <Button onClick={() => router.push("/review")}>Start review</Button>
  );

  return (
    <Layout>
      <Stack gap="lg">
        <div className="flex flex-col gap-2">
          <Heading as="h1" variant="display">
            Today
          </Heading>
          <Text variant="muted">
            Stay ahead with a focused queue, deep-work blocks, and Microsoft
            Graph health at a glance.
          </Text>
        </div>

        <ActionBar
          helperText="There are approvals waiting for you."
          primaryAction={primaryAction}
          secondaryActions={[
            <Link key="queue" href="/review">
              View queue
            </Link>,
          ]}
        />

        <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
          <Panel
            kicker="Approvals"
            title="Priority queue"
            description="Triage a handful of decisions designed for quick focus."
            footer={
              <Stack
                direction="horizontal"
                align="center"
                justify="between"
                className="text-sm text-[color:var(--ds-text-subtle)]"
              >
                <span>
                  Keyboard: <strong>A</strong> approve, <strong>E</strong> edit,{" "}
                  <strong>S</strong> skip, <strong>U</strong> undo
                </span>
                <Link
                  className="text-[color:var(--ds-text-accent)]"
                  href="/review"
                >
                  Open focus pane →
                </Link>
              </Stack>
            }
          >
            {approvals.length === 0 ? (
              <Text variant="muted">
                You’re all caught up. We’ll nudge you when something arrives.
              </Text>
            ) : (
              <Stack gap="sm">
                {approvals.map((approval) => (
                  <div
                    key={approval.id}
                    className="flex items-start justify-between gap-3 rounded-lg border border-[color:var(--ds-border-subtle)] bg-[color:var(--ds-surface)] p-3"
                  >
                    <div className="space-y-1">
                      <Text
                        variant="label"
                        className="text-[color:var(--ds-text-primary)]"
                      >
                        {approval.title || approval.summary || approval.id}
                      </Text>
                      {approval.due_at ? (
                        <Text variant="caption">
                          Due {new Date(approval.due_at).toLocaleTimeString()}
                        </Text>
                      ) : null}
                    </div>
                    <Badge tone="calm">Queued</Badge>
                  </div>
                ))}
              </Stack>
            )}
          </Panel>

          <Panel
            kicker="Focus blocks"
            title="Plan for today"
            description="Protect your most critical work windows."
          >
            {focusBlocks.length === 0 ? (
              <Text variant="muted">
                No focus sessions queued. Sync a plan from your calendar.
              </Text>
            ) : (
              <Stack gap="sm">
                {focusBlocks.map((block, index) => (
                  <div
                    key={`${block.time}-${index}`}
                    className="flex items-center justify-between rounded-lg bg-[color:var(--ds-surface-muted)] px-4 py-3"
                  >
                    <div>
                      <Text
                        variant="label"
                        className="text-[color:var(--ds-text-primary)]"
                      >
                        {block.label}
                      </Text>
                      <Text variant="caption">Deep work protected</Text>
                    </div>
                    <Badge tone="neutral" soft={false}>
                      {block.time || "Scheduled"}
                    </Badge>
                  </div>
                ))}
              </Stack>
            )}
          </Panel>

          <Panel
            kicker="Microsoft Graph"
            title="Connection health"
            tone="calm"
            description="Monitor sync freshness and keep approvals flowing."
            footer={
              <Stack direction="horizontal" justify="between" align="center">
                <Text variant="caption">
                  Need a reset? Check connection details and guided steps.
                </Text>
                <Link
                  className="text-[color:var(--ds-text-accent)]"
                  href="/connections"
                >
                  Go to connections →
                </Link>
              </Stack>
            }
          >
            {connection.state === "loading" ? (
              <Text variant="muted">Checking Microsoft Graph status…</Text>
            ) : null}

            {connection.state === "connected" ? (
              <Stack gap="sm">
                <div className="flex items-center justify-between rounded-lg bg-white/60 px-4 py-3 backdrop-blur dark:bg-slate-950/50">
                  <div>
                    <Text
                      variant="label"
                      className="text-[color:var(--ds-text-primary)]"
                    >
                      Connected
                    </Text>
                    <Text variant="caption">
                      {connection.expires_at
                        ? `Token refresh ${new Date(
                            connection.expires_at
                          ).toLocaleTimeString()}`
                        : "Token refresh scheduled"}
                    </Text>
                  </div>
                  <Badge tone="success">Healthy</Badge>
                </div>
                {connection.scopes?.length ? (
                  <Text variant="caption">
                    Scopes: {connection.scopes.join(", ")}
                  </Text>
                ) : null}
                {connection.tenant_id ? (
                  <Text variant="caption">Tenant {connection.tenant_id}</Text>
                ) : null}
              </Stack>
            ) : null}

            {connection.state === "disconnected" ? (
              <Stack gap="sm">
                <Text variant="muted">
                  {connection.reason ||
                    "Reconnect to resume syncing approvals."}
                </Text>
                <Button
                  variant="secondary"
                  onClick={() => router.push("/connections")}
                >
                  Reconnect
                </Button>
              </Stack>
            ) : null}

            {connection.state === "error" ? (
              <Stack gap="sm">
                <Text variant="muted">
                  {connection.message ||
                    "Something went wrong retrieving status."}
                </Text>
                <Button
                  variant="secondary"
                  onClick={() => router.push("/connections")}
                >
                  Troubleshoot
                </Button>
              </Stack>
            ) : null}
          </Panel>
        </div>
      </Stack>
    </Layout>
  );
}

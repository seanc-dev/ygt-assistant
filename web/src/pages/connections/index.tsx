import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  ActionBar,
  Badge,
  Button,
  Heading,
  Panel,
  Stack,
  Text,
} from "@lucid-work/ui";
import { Layout } from "../../components/Layout";
import LiveModeBanner from "../../components/LiveModeBanner";
import { Toast } from "../../components/Toast";
import { buildApiUrl } from "../../lib/apiBase";

type ConnectionStatus =
  | { connected: false; reason?: string }
  | {
      connected: true;
      scopes?: string[];
      expires_at?: string;
      tenant_id?: string;
      sync_history?: { ts: string; status: string }[];
      live?: boolean;
      live_flags?: {
        list_inbox?: boolean;
        send_mail?: boolean;
        create_events?: boolean;
      };
    };

export default function ConnectionsPage() {
  const [status, setStatus] = useState<ConnectionStatus>({ connected: false });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState("");

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(buildApiUrl("/connections/ms/status"), {
        credentials: "include",
      });
      const data = await res.json();
      setStatus(data);
    } catch (e: any) {
      setError(e?.message || "Failed to load status");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    window.localStorage.setItem(
      "ygt-connection-status",
      status.connected ? "connected" : "disconnected"
    );
  }, [status]);

  const syncHistory = useMemo(() => {
    if (!status.connected) return [];
    return status.sync_history || [];
  }, [status]);

  const handleConnect = () => {
    window.location.href = buildApiUrl("/connections/ms/oauth/start");
  };

  const handleDisconnect = async () => {
    await fetch(buildApiUrl("/connections/ms/disconnect"), {
      method: "POST",
      credentials: "include",
    });
    setToast("Disconnected");
    await refresh();
  };

  const handleTest = async () => {
    const res = await fetch(buildApiUrl("/connections/ms/test"), {
      method: "POST",
      credentials: "include",
    });
    const data = await res.json();
    setToast(data.ok ? "Graph test succeeded" : "Graph test failed");
    if (data && typeof data === "object") {
      setStatus(
        (prev) => {
          if (prev.connected) {
            // Preserve existing connected state properties
            return {
              ...prev,
              live: data.live,
              live_flags: data.live_flags,
            } as ConnectionStatus;
          } else {
            // Create new connected state from test data
            return {
              connected: !!data.ok,
              scopes: data.scopes,
              expires_at: data.expires_at,
              tenant_id: data.tenant_id,
              sync_history: data.sync_history,
              live: data.live,
              live_flags: data.live_flags,
            } as ConnectionStatus;
          }
        }
      );
    }
  };

  return (
    <Layout>
      <Stack gap="lg">
        <LiveModeBanner />
        <div className="flex flex-col gap-2">
          <Heading as="h1" variant="display">
            Connections
          </Heading>
          <Text variant="muted">
            Keep Microsoft Graph healthy and understand the sync cadence that
            feeds approvals.
          </Text>
        </div>

        <Panel
          kicker="Microsoft"
          title="Microsoft Graph"
          description="Mailbox, calendar, and directory signals"
          tone={status.connected ? "calm" : "soft"}
          actions={
            loading ? (
              <Badge tone="neutral">Checking…</Badge>
            ) : status.connected ? (
              <Badge tone="success">Connected</Badge>
            ) : (
              <Badge tone="warning">Action needed</Badge>
            )
          }
        >
          <Stack gap="md">
            {error ? <Text variant="muted">{error}</Text> : null}
            {status.connected ? (
              <Stack gap="sm">
                <Text variant="body">
                  Tenant {status.tenant_id || "unknown"} with scopes{" "}
                  {(status.scopes || []).join(", ") || "none"}.
                </Text>
                <Text variant="caption">
                  Token refresh{" "}
                  {status.expires_at
                    ? new Date(status.expires_at).toLocaleString()
                    : "scheduled"}
                </Text>
                {typeof status.live !== "undefined" ? (
                  <div className="text-xs text-[color:var(--ds-text-secondary)]">
                    <div>
                      Live slice: {status.live ? "enabled" : "disabled"}
                    </div>
                    {status.live_flags ? (
                      <ul className="list-disc pl-4">
                        <li>
                          Inbox: {status.live_flags.list_inbox ? "on" : "off"}
                        </li>
                        <li>
                          Send mail:{" "}
                          {status.live_flags.send_mail ? "on" : "off"}
                        </li>
                        <li>
                          Create events:{" "}
                          {status.live_flags.create_events ? "on" : "off"}
                        </li>
                      </ul>
                    ) : null}
                  </div>
                ) : null}
              </Stack>
            ) : (
              <Text variant="muted">
                {status.reason ||
                  "Connect Microsoft 365 to sync approvals and focus plans."}
              </Text>
            )}

            <ActionBar
              helperText={
                status.connected
                  ? "Stay connected while syncing"
                  : "No data flows until you’re connected"
              }
              primaryAction={
                status.connected ? (
                  <Button onClick={handleTest}>Run health check</Button>
                ) : (
                  <Button onClick={handleConnect}>Connect to Microsoft</Button>
                )
              }
              secondaryActions={[
                status.connected ? (
                  <Button
                    key="disconnect"
                    variant="ghost"
                    onClick={handleDisconnect}
                  >
                    Disconnect
                  </Button>
                ) : (
                  <Link key="learn" href="/history">
                    Review recent attempts
                  </Link>
                ),
              ]}
            />
          </Stack>
        </Panel>

        <Panel
          kicker="Sync history"
          title="Recent Graph syncs"
          description="See when Copilot last refreshed data"
        >
          {syncHistory.length === 0 ? (
            <Text variant="muted">No sync records yet.</Text>
          ) : (
            <Stack gap="sm">
              {syncHistory.map((item, index) => (
                <div
                  key={`${item.ts}-${index}`}
                  className="flex items-center justify-between rounded-lg border border-[color:var(--ds-border-subtle)] bg-[color:var(--ds-surface)] px-4 py-3"
                >
                  <div>
                    <Text variant="body">
                      {new Date(item.ts).toLocaleString()}
                    </Text>
                    <Text variant="caption">Status: {item.status}</Text>
                  </div>
                  <Badge tone={item.status === "ok" ? "success" : "warning"}>
                    {item.status}
                  </Badge>
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

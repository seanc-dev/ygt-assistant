import { Layout } from "../../components/Layout";
import { Card } from "../../components/Card";
import { useEffect, useState } from "react";

export default function ConnectionsPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<
    | { connected: false }
    | {
        connected: true;
        scopes?: string[];
        expires_at?: string;
        tenant_id?: string;
      }
  >({ connected: false });

  const api =
    process.env.NEXT_PUBLIC_ADMIN_API_BASE || "http://localhost:8000";
  const userId = "local-user"; // TODO: wire real session id later

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(
          `${api}/connections/ms/status?user_id=${encodeURIComponent(userId)}`
        );
        const data = await res.json();
        if (!cancelled) setStatus(data);
      } catch (e: any) {
        if (!cancelled) setError(e?.message || "Failed to load status");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [api]);
  return (
    <Layout>
      <h1 className="mb-4 text-2xl font-semibold">Connections</h1>
      <div className="grid gap-3 md:grid-cols-3">
        <Card
          title="Microsoft"
          subtitle="Mail and Calendar via Microsoft Graph."
          actions={
            <div className="flex flex-wrap items-center gap-2">
              {loading ? (
                <span className="text-sm text-slate-500">Loading…</span>
              ) : error ? (
                <span className="text-sm text-red-600">{error}</span>
              ) : status.connected ? (
                <>
                  <span className="rounded bg-green-100 px-2 py-0.5 text-xs text-green-700">
                    Connected
                  </span>
                  {"expires_at" in status && status.expires_at ? (
                    <span className="text-xs text-slate-500">
                      Expires {new Date(status.expires_at).toLocaleString()}
                    </span>
                  ) : null}
                  <button
                    onClick={async () => {
                      const res = await fetch(
                        `${api}/connections/ms/test?user_id=${encodeURIComponent(
                          userId
                        )}`,
                        { method: "POST" }
                      );
                      const data = await res.json();
                      alert(data.ok ? "Microsoft connection OK" : "Test failed");
                    }}
                    className="rounded border px-3 py-1 text-sm"
                  >
                    Test
                  </button>
                  <button
                    onClick={async () => {
                      await fetch(
                        `${api}/connections/ms/disconnect?user_id=${encodeURIComponent(
                          userId
                        )}`,
                        { method: "POST" }
                      );
                      // refresh status
                      setLoading(true);
                      const res = await fetch(
                        `${api}/connections/ms/status?user_id=${encodeURIComponent(
                          userId
                        )}`
                      );
                      setStatus(await res.json());
                      setLoading(false);
                    }}
                    className="rounded border px-3 py-1 text-sm"
                  >
                    Disconnect
                  </button>
                </>
              ) : (
                <>
                  <a
                    href={`${api}/connections/ms/oauth/start?user_id=${encodeURIComponent(
                      userId
                    )}`}
                    className="rounded bg-slate-900 px-3 py-1 text-sm text-white dark:bg-slate-100 dark:text-slate-900"
                  >
                    Connect
                  </a>
                  <button
                    onClick={async () => {
                      const res = await fetch(
                        `${api}/connections/ms/test?user_id=${encodeURIComponent(
                          userId
                        )}`,
                        { method: "POST" }
                      );
                      const data = await res.json();
                      alert(data.ok ? "Not connected (OK)" : "Test failed");
                    }}
                    className="rounded border px-3 py-1 text-sm"
                  >
                    Test
                  </button>
                </>
              )}
            </div>
          }
        />
      </div>
    </Layout>
  );
}

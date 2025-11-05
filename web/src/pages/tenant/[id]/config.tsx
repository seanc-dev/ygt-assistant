import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/router";
import { api } from "../../../lib/api";
import { normalizeNotionIdFromString } from "../../../lib/notionId";
import { Button } from "../../../components/Button";
import { Label } from "../../../components/Form/Label";
import { Textarea } from "../../../components/Form/Textarea";
import { Badge } from "../../../components/Badge";

const TEMPLATE_YAML = `features:
  sessions_value: true        # allow Sessions.Value to be written
  programs: false             # reserved for future
  sales: false                # reserved for future

currency:
  code: "NZD"                 # used for display/logging only

notion:
  tasks:
    db_id: "<TASKS_DB_ID>"
    props:
      title: "Name"                 # Title
      status: "Status"              # Select: Inbox, Next, In-Progress, Waiting, Done
      due: "Due"                    # Date
      assignee: "Assignee"          # People
      priority: "Priority"          # Select: Low, Med, High
      client_rel: "Client"          # Relation -> Clients.Name (optional)
      source: "Source"              # Select: Email, Calendar, Manual
      source_id: "Source ID"        # Text
      email_url: "Email URL"        # URL
      notes: "Notes"                # Rich text
  clients:
    db_id: "<CLIENTS_DB_ID>"
    props:
      title: "Name"                 # Title
      email: "Email"                # Email
      company: "Company"            # Text (optional)
      owner: "Owner"                # People (optional)
      stage: "Stage"                # Select: Lead, Active, Dormant
      last_contacted: "Last Contacted" # Date
      sessions_rel: "Sessions"      # Relation -> Sessions.Title
      total_value_rollup: "Total Value (optional)"  # Rollup (read-only)
      notes: "Notes"                # Rich text
  sessions:
    db_id: "<SESSIONS_DB_ID>"
    props:
      title: "Title"                # Title
      client_rel: "Client"          # Relation -> Clients.Name
      date: "Date"                  # Date
      summary: "Summary"            # Rich text
      transcript_url: "Transcript URL"  # URL
      duration_min: "Duration (min)"    # Number
      value: "Value (optional)"         # Number (currency) — written only if features.sessions_value=true
      tags: "Tags"                  # Multi-select

defaults:
  task_status_new: "Inbox"
  session_value_round: 0            # 0 or 2 typical`;

const API_BASE =
  process.env.NEXT_PUBLIC_ADMIN_API_BASE || "https://api.lucid-work.com";

type ValidationResult = {
  ok?: boolean;
  error?: string;
  databases?: Record<string, any>;
  [key: string]: unknown;
} | null;

export default function TenantConfig() {
  const router = useRouter();
  const { id } = router.query;
  const tenantId = typeof id === "string" ? id : "";
  const [yaml, setYaml] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [validating, setValidating] = useState(false);
  const [validationResult, setValidationResult] = useState<ValidationResult>(null);
  const [error, setError] = useState<string | null>(null);

  const loadConfig = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await api.getConfig(tenantId);
      setYaml(result.yaml || "");
    } catch (err) {
      setError("Failed to load config");
    } finally {
      setLoading(false);
    }
  }, [tenantId]);

  useEffect(() => {
    if (tenantId) {
      void loadConfig();
    }
  }, [tenantId, loadConfig]);

  const saveConfig = async () => {
    try {
      setSaving(true);
      setError(null);
      await api.setConfig(tenantId, yaml);
    } catch (err: any) {
      setError(err.message || "Failed to save config");
    } finally {
      setSaving(false);
    }
  };

  const validateConfig = async () => {
    try {
      setValidating(true);
      setError(null);
      const result = await api.validateNotionConfig(tenantId);
      setValidationResult(result);
    } catch (err: any) {
      setError(err.message || "Failed to validate config");
    } finally {
      setValidating(false);
    }
  };

  const insertTemplate = () => {
    setYaml(TEMPLATE_YAML);
  };

  const replaceDbId = (section: "tasks" | "clients" | "sessions") => {
    const link = window.prompt(`Paste Notion link for ${section} database`);
    if (!link) return;
    const notionId = normalizeNotionIdFromString(link);
    if (!notionId) {
      window.alert("Could not extract a Notion ID from that link");
      return;
    }
    const re = new RegExp(`(\\n\\s*${section}:\\s*\\n\\s*db_id:\\s*")(.*?)(\")`);
    if (re.test(yaml)) {
      setYaml(yaml.replace(re, (_m, p1, _old, p3) => `${p1}${notionId}${p3}`));
    } else {
      window.alert(`Could not find ${section}.db_id in YAML; please insert manually.`);
    }
  };

  const toggleSessionsValue = () => {
    const lines = yaml.split("\n");
    const next = lines.map((line) => {
      if (line.trim().startsWith("sessions_value:")) {
        const current = line.includes("true");
        return line.replace(/true|false/, current ? "false" : "true");
      }
      return line;
    });
    setYaml(next.join("\n"));
  };

  const updateCurrency = (code: string) => {
    const lines = yaml.split("\n");
    const next = lines.map((line) => {
      if (line.trim().startsWith("code:")) {
        return line.replace(/"[^"]*"/, `"${code}"`);
      }
      return line;
    });
    setYaml(next.join("\n"));
  };

  const updateValueRound = (round: number) => {
    const lines = yaml.split("\n");
    const next = lines.map((line) => {
      if (line.trim().startsWith("session_value_round:")) {
        return line.replace(/\d+/, round.toString());
      }
      return line;
    });
    setYaml(next.join("\n"));
  };

  const currencyCode = useMemo(() => yaml.match(/code: "([^"]*)"/)?.[1] || "NZD", [yaml]);
  const valueRound = useMemo(
    () => yaml.match(/session_value_round: (\d+)/)?.[1] || "0",
    [yaml]
  );

  if (loading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-50">
        <p className="text-sm text-slate-500">Loading…</p>
      </main>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <main className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
        <div className="flex flex-col gap-6">
          <header className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-3xl font-semibold text-slate-900">Notion configuration — {tenantId}</h1>
              <Badge tone="info">Advanced</Badge>
            </div>
            <p className="text-sm text-slate-600">
              Configure database mappings and feature flags. Validate the setup after making
              changes.
            </p>
          </header>

          {error ? (
            <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 shadow-sm">
              {error}
            </div>
          ) : null}

          <section className="grid grid-cols-1 gap-6 lg:grid-cols-[320px,1fr]">
            <div className="space-y-4">
              <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
                <h2 className="text-lg font-semibold text-slate-900">Quick controls</h2>
                <div className="mt-4 space-y-3 text-sm">
                  <label className="flex items-center gap-2 text-slate-700">
                    <input
                      type="checkbox"
                      checked={yaml.includes("sessions_value: true")}
                      onChange={toggleSessionsValue}
                      className="h-4 w-4 rounded border-slate-300 text-primary-600 focus:outline-none focus:ring-2 focus:ring-primary-500"
                    />
                    Enable sessions value field
                  </label>
                  <div className="space-y-1">
                    <Label className="text-xs uppercase tracking-wide text-slate-500">
                      Currency
                    </Label>
                    <select
                      value={currencyCode}
                      onChange={(event) => updateCurrency(event.target.value)}
                      className="focus-outline block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm"
                    >
                      <option value="NZD">NZD</option>
                      <option value="USD">USD</option>
                      <option value="AUD">AUD</option>
                      <option value="EUR">EUR</option>
                    </select>
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs uppercase tracking-wide text-slate-500">
                      Value rounding
                    </Label>
                    <select
                      value={valueRound}
                      onChange={(event) => updateValueRound(parseInt(event.target.value, 10))}
                      className="focus-outline block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm"
                    >
                      <option value="0">No rounding</option>
                      <option value="2">Round to 2 decimals</option>
                    </select>
                  </div>
                </div>
              </div>

              <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
                <h2 className="text-lg font-semibold text-slate-900">Actions</h2>
                <div className="mt-4 space-y-3 text-sm">
                  <Button type="button" variant="outline" className="w-full" onClick={insertTemplate}>
                    Insert template
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    className="w-full"
                    onClick={validateConfig}
                    disabled={validating}
                  >
                    {validating ? "Validating…" : "Validate config"}
                  </Button>
                  <Button
                    type="button"
                    className="w-full"
                    onClick={saveConfig}
                    disabled={saving}
                  >
                    {saving ? "Saving…" : "Save config"}
                  </Button>
                  <div className="grid gap-2 pt-2">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => replaceDbId("tasks")}
                    >
                      Parse Notion link → tasks.db_id
                    </Button>
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => replaceDbId("clients")}
                    >
                      Parse Notion link → clients.db_id
                    </Button>
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => replaceDbId("sessions")}
                    >
                      Parse Notion link → sessions.db_id
                    </Button>
                  </div>
                </div>
              </div>

              <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
                <h2 className="text-lg font-semibold text-slate-900">Navigation</h2>
                <div className="mt-4 flex flex-col gap-2 text-sm">
                  <Link
                    href={`/tenant/${tenantId}/setup`}
                    className="focus-outline inline-flex items-center justify-center rounded-md border border-slate-200 bg-white px-3 py-2 font-medium text-slate-700 shadow-sm transition hover:border-primary-300 hover:text-primary-700"
                  >
                    Back to setup
                  </Link>
                  <Link
                    href="/"
                    className="focus-outline inline-flex items-center justify-center rounded-md border border-slate-200 bg-white px-3 py-2 font-medium text-slate-700 shadow-sm transition hover:border-primary-300 hover:text-primary-700"
                  >
                    Back to tenants
                  </Link>
                </div>
              </div>
            </div>

            <div className="space-y-6">
              <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
                <div className="border-b border-slate-200 p-5">
                  <h2 className="text-lg font-semibold text-slate-900">YAML configuration</h2>
                  <p className="mt-1 text-sm text-slate-600">
                    Edit the YAML mapping directly. Use the quick controls for common tasks.
                  </p>
                </div>
                <div className="p-5">
                  <Textarea
                    value={yaml}
                    onChange={(event) => setYaml(event.target.value)}
                    className="h-[28rem] font-mono"
                    placeholder="Paste your Notion configuration YAML here..."
                  />
                </div>
              </section>

              {validationResult ? (
                <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
                  <h2 className="text-lg font-semibold text-slate-900">Validation results</h2>
                  <div className="mt-4 space-y-4 text-sm">
                    {validationResult.error === "no_notion_connection" ? (
                      <div className="space-y-3">
                        <div className="rounded-md border border-amber-200 bg-amber-50 p-3 text-amber-800">
                          Notion is not connected yet. Connect to proceed.
                        </div>
                        <a
                          className="focus-outline inline-flex items-center rounded-md border border-slate-200 bg-white px-3 py-2 font-medium text-slate-700 shadow-sm transition hover:border-primary-300 hover:text-primary-700"
                          href={`${API_BASE}/oauth/notion/start?tenant_id=${tenantId}`}
                        >
                          Connect Notion
                        </a>
                      </div>
                    ) : validationResult.ok ? (
                      <div className="rounded-md border border-emerald-200 bg-emerald-50 p-3 text-emerald-700">
                        ✅ All databases and properties are valid
                      </div>
                    ) : (
                      <div className="space-y-4">
                        {Object.entries(validationResult.databases || {}).map(
                          ([dbName, dbInfo]) => (
                            <div key={dbName} className="rounded-lg border border-slate-200 p-4 shadow-sm">
                              <div className="flex items-center justify-between">
                                <h3 className="text-base font-semibold text-slate-900 capitalize">
                                  {dbName} database
                                </h3>
                                {dbInfo.ok ? (
                                  <span className="text-sm text-emerald-600">✅ Valid</span>
                                ) : (
                                  <span className="text-sm text-red-600">❌ Invalid</span>
                                )}
                              </div>
                              <div className="mt-2 space-y-1 text-sm text-slate-600">
                                <p>Title: {dbInfo.title || "Unknown"}</p>
                                <p>DB ID: {dbInfo.db_id}</p>
                                {dbInfo.missing_props?.length > 0 ? (
                                  <p className="text-red-600">
                                    Missing properties: {dbInfo.missing_props.join(", ")}
                                  </p>
                                ) : null}
                                {dbInfo.error ? (
                                  <p className="text-red-600">Error: {dbInfo.error}</p>
                                ) : null}
                              </div>
                            </div>
                          )
                        )}
                      </div>
                    )}
                  </div>
                </section>
              ) : null}
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}

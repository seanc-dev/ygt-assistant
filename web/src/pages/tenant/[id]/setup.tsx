import Link from "next/link";
import { useRouter } from "next/router";
import { useEffect, useMemo, useState } from "react";
import useSWR from "swr";
import { api } from "../../../lib/api";
import { normalizeNotionIdFromString } from "../../../lib/notionId";
import { Button } from "../../../components/Button";
import { Field } from "../../../components/Form/Field";
import { Label } from "../../../components/Form/Label";
import { Badge } from "../../../components/Badge";

type TenantSettings = {
  client_email?: string;
  notion_tasks_db_id?: string;
  notion_crm_db_id?: string;
  notion_sessions_db_id?: string;
};

type StatusResponse = {
  overall_status?: "complete" | "partial" | "blocked";
  has_client_email?: boolean;
  has_notion_connection?: boolean;
  has_db_ids?: boolean;
  has_nylas_connection?: boolean;
};

type SettingsResponse = {
  name?: string;
  settings?: TenantSettings;
  status?: StatusResponse;
};

const DEFAULT_NOTION_IDS = {
  notion_tasks_db_id: "26fd2f03d34580af8c88c3d9bc009e0c",
  notion_crm_db_id: "26fd2f03d345803e8a2fe708df8d8773",
  notion_sessions_db_id: "26fd2f03d3458027bafeee06358df67b",
} as const;

const statusTone: Record<string, "success" | "warning" | "neutral"> = {
  complete: "success",
  partial: "warning",
  blocked: "neutral",
};

const statusBanner: Record<string, string> = {
  complete: "border-emerald-200 bg-emerald-50 text-emerald-800",
  partial: "border-amber-200 bg-amber-50 text-amber-800",
  blocked: "border-slate-200 bg-slate-50 text-slate-700",
};

type MessageState = { tone: "success" | "danger"; text: string } | null;

async function apiGetSettings(tenantId: string) {
  const response = await fetch(
    `${process.env.NEXT_PUBLIC_ADMIN_API_BASE}/admin/tenants/${tenantId}/settings`,
    { credentials: "include" }
  );
  if (response.status === 401) {
    throw new Error("unauthorized");
  }
  return response.json();
}

export default function Setup() {
  const router = useRouter();
  const { id: rawId } = router.query;
  const id = typeof rawId === "string" ? rawId : "";
  const { data, mutate } = useSWR<SettingsResponse>(
    id ? ["settings", id] : null,
    () => apiGetSettings(id)
  );
  const { data: me, error: meError } = useSWR("me", api.me);

  const [form, setForm] = useState<TenantSettings>({
    client_email: "",
    ...DEFAULT_NOTION_IDS,
  });
  const [message, setMessage] = useState<MessageState>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isInviting, setIsInviting] = useState(false);
  const [isIssuing, setIsIssuing] = useState(false);
  const [isCheckingRules, setIsCheckingRules] = useState(false);

  const hasNotion = Boolean(data?.status?.has_notion_connection);
  const hasNylas = Boolean(data?.status?.has_nylas_connection);

  useEffect(() => {
    if (data?.settings) {
      setForm((prev) => ({ ...prev, ...data.settings }));
    }
  }, [data]);

  useEffect(() => {
    if (meError) router.push("/login");
  }, [meError, router]);

  useEffect(() => {
    setMessage(null);
  }, [id]);

  const status = data?.status ?? {};
  const overall = status.overall_status ?? "blocked";
  const tone = statusTone[overall] ?? "neutral";

  const parsedLinks = useMemo(
    () => [
      {
        key: "notion_tasks_db_id" as const,
        label: "Tasks database ID",
      },
      {
        key: "notion_crm_db_id" as const,
        label: "Clients database ID",
      },
      {
        key: "notion_sessions_db_id" as const,
        label: "Sessions database ID",
      },
    ],
    []
  );

  const updateField = (key: keyof TenantSettings, value: string) => {
    setForm((previous) => ({ ...previous, [key]: value }));
  };

  const parseNotionLinkAny = () => {
    const link = window.prompt("Paste Notion database link");
    if (!link) return;
    const extracted = normalizeNotionIdFromString(link);
    if (!extracted) {
      window.alert("Could not extract a Notion ID from that link");
      return;
    }
    const choice = (
      window.prompt(
        "Apply to which field? Enter one of: tasks, crm, sessions, all",
        "tasks"
      ) || ""
    )
      .trim()
      .toLowerCase();
    const map: Record<string, keyof TenantSettings | "all"> = {
      tasks: "notion_tasks_db_id",
      crm: "notion_crm_db_id",
      sessions: "notion_sessions_db_id",
      all: "all",
    };
    const target = map[choice];
    if (!target) {
      window.alert("Invalid choice. Use: tasks, crm, sessions, or all");
      return;
    }
    if (target === "all") {
      setForm((prev) => ({
        ...prev,
        notion_tasks_db_id: extracted,
        notion_crm_db_id: extracted,
        notion_sessions_db_id: extracted,
      }));
    } else {
      setForm((prev) => ({ ...prev, [target]: extracted }));
    }
  };

  const extractErrorDetail = async (response: Response) => {
    try {
      const json = await response.clone().json();
      const detail = (json as { detail?: unknown }).detail;
      if (!detail) return "";
      return typeof detail === "string" ? detail : JSON.stringify(detail);
    } catch {
      try {
        return await response.text();
      } catch {
        return "";
      }
    }
  };

  const handleSave = async () => {
    if (!id) return;
    setMessage(null);
    setIsSaving(true);
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_ADMIN_API_BASE}/admin/tenants/${id}/settings`,
        {
          method: "PUT",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ data: form }),
        }
      );
      if (response.status === 401) {
        router.push("/login");
        return;
      }
      if (!response.ok) {
        const detail = await extractErrorDetail(response);
        throw new Error(
          `Save failed (${response.status} ${response.statusText})${
            detail ? `: ${detail}` : ""
          }`
        );
      }
      await mutate();
      setMessage({ tone: "success", text: "Settings saved" });
    } catch (error) {
      const text =
        error instanceof Error
          ? error.message
          : "Save request failed. Please try again.";
      setMessage({ tone: "danger", text });
    } finally {
      setIsSaving(false);
    }
  };

  const handleInvite = async () => {
    if (!id) return;
    setMessage(null);
    setIsInviting(true);
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_ADMIN_API_BASE}/admin/tenants/${id}/invite`,
        {
          method: "POST",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ to_email: form.client_email }),
        }
      );
      if (!response.ok) {
        const detail = await extractErrorDetail(response);
        throw new Error(
          `Invite failed (${response.status} ${response.statusText})${
            detail ? `: ${detail}` : ""
          }`
        );
      }
      const json = await response.json();
      setMessage({
        tone: "success",
        text: `Invite sent. Notion link: ${
          json.links?.notion ?? ""
        } • Email link: ${json.links?.nylas ?? ""}`,
      });
    } catch (error) {
      const text =
        error instanceof Error
          ? error.message
          : "Invite request failed. Please try again.";
      setMessage({ tone: "danger", text });
    } finally {
      setIsInviting(false);
    }
  };

  const handleIssueCredentials = async () => {
    if (!id) return;
    setMessage(null);
    setIsIssuing(true);
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_ADMIN_API_BASE}/admin/tenants/${id}/issue-credentials`,
        {
          method: "POST",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email: form.client_email }),
        }
      );
      if (!response.ok) {
        throw new Error(`${response.status} ${response.statusText}`);
      }
      setMessage({
        tone: "success",
        text: "Credentials issued and emailed",
      });
    } catch (error) {
      const text =
        error instanceof Error
          ? error.message
          : "Issue credentials failed. Please try again.";
      setMessage({ tone: "danger", text });
    } finally {
      setIsIssuing(false);
    }
  };

  const handleApplyStandardRules = async () => {
    if (!id) return;
    setMessage(null);
    setIsCheckingRules(true);
    try {
      let sampleText = "";
      const sampleRes = await fetch(
        `${process.env.NEXT_PUBLIC_ADMIN_API_BASE}/config/rules.sample.yaml`,
        { credentials: "include" }
      );
      if (sampleRes.ok) {
        sampleText = await sampleRes.text();
      } else if (sampleRes.status === 404) {
        // Fallback to admin-ui public assets if API does not serve the file
        const alt = await fetch(`/config/rules.sample.yaml`);
        if (!alt.ok) {
          throw new Error(
            `Failed to load sample rules (API: ${sampleRes.status} ${sampleRes.statusText}, UI: ${alt.status} ${alt.statusText})`
          );
        }
        sampleText = await alt.text();
      } else {
        throw new Error(
          `Failed to load sample rules (${sampleRes.status} ${sampleRes.statusText})`
        );
      }
      const sampleYaml = sampleText.trim();

      try {
        await api.setRules(id, sampleYaml);
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        if (msg.startsWith("401 ")) {
          router.push("/login");
          return;
        }
        throw err;
      }
      setMessage({
        tone: "success",
        text: "Standard rules applied successfully. Visit the Rules page to customize if needed.",
      });
    } catch (error) {
      const text =
        error instanceof Error
          ? error.message
          : "Failed to apply standard rules.";
      setMessage({ tone: "danger", text });
    } finally {
      setIsCheckingRules(false);
    }
  };

  if (!id) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-50">
        <p className="text-sm text-slate-500">Loading…</p>
      </main>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <main className="mx-auto max-w-5xl px-4 py-10 sm:px-6">
        <div className="flex flex-col gap-6">
          <header className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-3xl font-semibold text-slate-900">
                Setup — {data?.name ?? id}
              </h1>
              <Badge tone={tone}>{overall}</Badge>
            </div>
            <p className="text-sm text-slate-600">
              Configure contact details and Notion integrations before inviting
              the tenant.
            </p>
          </header>

          <div
            className={`rounded-lg border p-4 text-sm shadow-sm ${
              statusBanner[overall] ?? statusBanner.blocked
            }`}
          >
            {overall === "complete" &&
              "All set. You can re-send the invite if needed."}
            {overall === "partial" && "A few steps remain to complete setup."}
            {overall === "blocked" &&
              "Let’s get you set up. Start by adding a contact email and database IDs."}
          </div>

          {message ? (
            <div
              role="status"
              className={`rounded-lg border p-4 text-sm ${
                message.tone === "success"
                  ? "border-emerald-200 bg-emerald-50 text-emerald-800"
                  : "border-red-200 bg-red-50 text-red-700"
              }`}
            >
              {message.text}
            </div>
          ) : null}

          <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-900">
              Client contact
            </h2>
            <p className="mt-1 text-sm text-slate-600">
              We’ll send invites and credentials to this email address.
            </p>
            <div className="mt-4 max-w-md">
              <Label htmlFor="client-email">Client email</Label>
              <Field
                id="client-email"
                type="email"
                placeholder="alex@example.com"
                value={form.client_email ?? ""}
                onChange={(event) =>
                  updateField("client_email", event.target.value)
                }
              />
            </div>
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-900">
              Notion database IDs
            </h2>
            <p className="mt-1 text-sm text-slate-600">
              Paste the database ID directly or provide a share link to extract
              it automatically.
            </p>
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              {parsedLinks.map(({ key, label }) => (
                <div key={key} className="space-y-2">
                  <Label htmlFor={key}>{label}</Label>
                  <Field
                    id={key}
                    value={form[key] ?? ""}
                    placeholder="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                    onChange={(event) => updateField(key, event.target.value)}
                  />
                </div>
              ))}
            </div>
            <div className="mt-4">
              <Button
                variant="secondary"
                onClick={parseNotionLinkAny}
                type="button"
              >
                Parse Notion links
              </Button>
            </div>
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-900">Next steps</h2>
            <p className="mt-1 text-sm text-slate-600">
              Save changes before inviting the client or issuing login
              credentials.
            </p>
            <div className="mt-4 flex flex-wrap gap-3">
              <Button onClick={handleSave} disabled={isSaving} type="button">
                {isSaving ? "Saving…" : "Save"}
              </Button>
              <Button
                onClick={handleInvite}
                disabled={!form.client_email || isInviting}
                type="button"
              >
                {isInviting ? "Sending invite…" : "Send invite"}
              </Button>
              <Button
                onClick={handleIssueCredentials}
                disabled={!form.client_email || isIssuing}
                type="button"
              >
                {isIssuing ? "Issuing…" : "Issue login credentials"}
              </Button>
              <Link
                href={`/tenant/${id}/config`}
                className="focus-outline inline-flex items-center rounded-md border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm transition hover:border-primary-300 hover:text-primary-700"
              >
                Configure Notion
              </Link>
              <Link
                href="/"
                className="focus-outline inline-flex items-center rounded-md border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm transition hover:border-primary-300 hover:text-primary-700"
              >
                Back to tenants
              </Link>
            </div>

            <div className="mt-6 flex flex-wrap gap-3 text-sm">
              <a
                className={`focus-outline inline-flex items-center rounded-md border border-slate-200 px-4 py-2 text-sm font-medium shadow-sm transition ${
                  hasNotion
                    ? "cursor-not-allowed bg-slate-100 text-slate-400"
                    : "bg-white text-slate-700 hover:border-primary-300 hover:text-primary-700"
                }`}
                href={
                  hasNotion
                    ? undefined
                    : `${process.env.NEXT_PUBLIC_ADMIN_API_BASE}/connect?provider=notion&tenant_id=${id}`
                }
                aria-disabled={hasNotion}
                onClick={(e) => {
                  if (hasNotion) e.preventDefault();
                }}
                target={hasNotion ? undefined : "_blank"}
                rel={hasNotion ? undefined : "noreferrer"}
              >
                {hasNotion ? "Notion connected" : "Connect Notion"}
              </a>
              <a
                className={`focus-outline inline-flex items-center rounded-md border border-slate-200 px-4 py-2 text-sm font-medium shadow-sm transition ${
                  hasNylas
                    ? "cursor-not-allowed bg-slate-100 text-slate-400"
                    : "bg-white text-slate-700 hover:border-primary-300 hover:text-primary-700"
                }`}
                href={
                  hasNylas
                    ? undefined
                    : `${process.env.NEXT_PUBLIC_ADMIN_API_BASE}/oauth/nylas/start?provider=google&tenant_id=${id}`
                }
                aria-disabled={hasNylas}
                onClick={(e) => {
                  if (hasNylas) e.preventDefault();
                }}
                target={hasNylas ? undefined : "_blank"}
                rel={hasNylas ? undefined : "noreferrer"}
              >
                {hasNylas
                  ? "Email & calendar connected"
                  : "Connect email & calendar"}
              </a>
              <Button
                onClick={handleApplyStandardRules}
                disabled={isCheckingRules}
                variant="ghost"
                type="button"
              >
                {isCheckingRules ? "Applying rules…" : "Apply Standard Rules"}
              </Button>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}

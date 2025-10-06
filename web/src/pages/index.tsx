import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import useSWR from "swr";
import { api } from "../lib/api";
import { Button } from "../components/Button";
import { Field } from "../components/Form/Field";
import { Label } from "../components/Form/Label";
import { Badge } from "../components/Badge";
import { ThemeToggle } from "@coachflow/ui";

type TenantStatus = {
  overall_status?: "complete" | "partial" | "blocked";
  has_client_email?: boolean;
  has_notion_connection?: boolean;
  has_db_ids?: boolean;
  has_nylas_connection?: boolean;
};

type Tenant = {
  id: string;
  name: string;
  status?: TenantStatus;
};

type TenantsResponse = {
  tenants: Tenant[];
};

const statusTone: Record<string, "success" | "warning" | "neutral"> = {
  complete: "success",
  partial: "warning",
  blocked: "neutral",
};

const readinessCopy: Record<string, string> = {
  complete: "Ready for launch",
  partial: "Still needs attention",
  blocked: "Setup pending",
};

export default function Home() {
  const router = useRouter();
  const { data: me, error: meError } = useSWR("me", api.me);
  const { data: tenants, mutate } = useSWR<TenantsResponse>(
    me ? "tenants" : null,
    api.tenantsList
  );
  const [newTenantName, setNewTenantName] = useState("");
  const [isCreatingTenant, setIsCreatingTenant] = useState(false);

  useEffect(() => {
    if (meError) router.push("/login");
  }, [meError, router]);

  const handleCreateTenant = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!newTenantName.trim()) return;
    try {
      setIsCreatingTenant(true);
      await api.createTenant(newTenantName.trim());
      setNewTenantName("");
      await mutate();
    } finally {
      setIsCreatingTenant(false);
    }
  };

  if (!me) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-50 dark:bg-slate-950">
        <div className="text-center">
          <p className="text-sm text-slate-500 dark:text-slate-400">Loading…</p>
          <p className="text-xs text-slate-400 dark:text-slate-500 mt-2">
            {meError ? `Error: ${meError.message}` : 'Checking authentication...'}
          </p>
        </div>
      </main>
    );
  }

  const tenantList = tenants?.tenants ?? [];

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
      <main className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
        <div className="flex flex-col gap-8">
          <header className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="space-y-2">
              <h1 className="text-3xl font-semibold text-slate-900 dark:text-slate-100">Tenants</h1>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                Review onboarding progress, update configuration, and trigger invites.
              </p>
            </div>
            <ThemeToggle
              className="focus-outline inline-flex h-9 w-9 items-center justify-center rounded-md border border-slate-200 bg-white text-slate-600 transition hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
              inactiveLabel="Switch to dark theme"
              activeLabel="Switch to light theme"
            />
          </header>

          <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800">
            <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Create a new tenant</h2>
            <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
              Tenants manage their own integrations and rules. Provide a descriptive name to
              get started.
            </p>
            <form
              className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-end"
              onSubmit={handleCreateTenant}
            >
              <div className="flex-1">
                <Label htmlFor="tenant-name">Tenant name</Label>
                <Field
                  id="tenant-name"
                  placeholder="Acme Coaching"
                  value={newTenantName}
                  onChange={(event) => setNewTenantName(event.target.value)}
                  required
                />
              </div>
              <Button type="submit" className="sm:w-auto" disabled={isCreatingTenant}>
                {isCreatingTenant ? "Creating…" : "Create tenant"}
              </Button>
            </form>
          </section>

          <section className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Current tenants</h2>
              <div className="hidden items-center gap-2 text-xs text-slate-500 dark:text-slate-400 sm:flex">
                <Badge tone="success">complete</Badge>
                <Badge tone="warning">partial</Badge>
                <Badge tone="neutral">blocked</Badge>
              </div>
            </div>

            {tenantList.length === 0 ? (
              <div className="rounded-lg border border-dashed border-slate-300 bg-white p-8 text-center text-sm text-slate-500 dark:border-slate-600 dark:text-slate-400">
                No tenants yet. Create one above to begin onboarding.
              </div>
            ) : (
              <div className="space-y-4">
                {tenantList.map((tenant) => {
                  const status = tenant.status ?? {};
                  const overall = status.overall_status ?? "blocked";
                  const tone = statusTone[overall] ?? "neutral";
                  return (
                    <article
                      key={tenant.id}
                      className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800"
                    >
                      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                        <div className="space-y-2">
                          <div className="flex flex-wrap items-center gap-2">
                            <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">{tenant.name}</h3>
                            <Badge tone={tone}>{overall}</Badge>
                          </div>
                          <p className="text-sm text-slate-500 dark:text-slate-400">{tenant.id}</p>
                          <p className="text-sm text-slate-600 dark:text-slate-400">
                            {readinessCopy[overall] ?? "Awaiting setup"}
                          </p>
                          <div className="flex flex-wrap gap-2 pt-2">
                            <Badge tone={status.has_client_email ? "success" : "neutral"}>
                              Contact
                            </Badge>
                            <Badge tone={status.has_notion_connection ? "success" : "neutral"}>
                              Notion
                            </Badge>
                            <Badge tone={status.has_db_ids ? "success" : "neutral"}>DB IDs</Badge>
                            <Badge tone={status.has_nylas_connection ? "success" : "neutral"}>
                              Email
                            </Badge>
                          </div>
                        </div>

                        <div className="flex flex-wrap items-center gap-2">
                          <Link
                            href={`/tenant/${tenant.id}/rules`}
                            className="focus-outline inline-flex items-center rounded-md border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 shadow-sm transition hover:border-primary-300 hover:text-primary-700"
                          >
                            Rules
                          </Link>
                          <Link
                            href={`/tenant/${tenant.id}/triage`}
                            className="focus-outline inline-flex items-center rounded-md border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 shadow-sm transition hover:border-primary-300 hover:text-primary-700"
                          >
                            Triage
                          </Link>
                          <Link
                            href={`/tenant/${tenant.id}/setup`}
                            className="focus-outline inline-flex items-center rounded-md border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 shadow-sm transition hover:border-primary-300 hover:text-primary-700"
                          >
                            Setup
                          </Link>
                        </div>
                      </div>
                    </article>
                  );
                })}
              </div>
            )}
          </section>
        </div>
      </main>
    </div>
  );
}

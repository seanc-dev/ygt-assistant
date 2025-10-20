import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { Layout } from "../components/Layout";
import { Card } from "../components/Card";

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
  const [approvals, setApprovals] = useState<any[]>([]);
  const [plan, setPlan] = useState<string[]>([]);

  useEffect(() => {
    api
      .approvals("all")
      .then((res) => setApprovals((res || []).slice(0, 3)))
      .catch(() => setApprovals([]));
    fetch(
      `${
        process.env.NEXT_PUBLIC_ADMIN_API_BASE || "https://api.ygt-assistant.com"
      }/calendar/plan-today`,
      { credentials: "include" }
    )
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((d) =>
        setPlan(
          (d.plan || []).map(
            (i: any) => `${i.time || "10:00"} ${i.title || "Focus"}`
          )
        )
      )
      .catch(() => setPlan([]));
  }, []);

  return (
    <Layout>
      <h1 className="mb-4 text-2xl font-semibold">Home</h1>
      <div className="grid gap-4 md:grid-cols-2">
        <Card
          title="Now"
          subtitle="What matters most right now"
          actions={
            <Link
              href="/review"
              className="rounded bg-slate-900 px-3 py-1 text-sm text-white dark:bg-slate-100 dark:text-slate-900"
            >
              Start review
            </Link>
          }
        >
          <ul className="list-disc pl-5 text-sm text-slate-700 dark:text-slate-300">
            {approvals.length === 0 ? (
              <li>No pending approvals</li>
            ) : (
              approvals.map((a) => (
                <li key={a.id}>{a.title || a.summary || a.id}</li>
              ))
            )}
          </ul>
        </Card>
        <Card title="Suggested focus" subtitle="90 minutes">
          <ul className="list-disc pl-5 text-sm text-slate-700 dark:text-slate-300">
            {plan.length === 0 ? (
              <li>No plan yet</li>
            ) : (
              plan.map((p, i) => <li key={i}>{p}</li>)
            )}
          </ul>
        </Card>
      </div>
    </Layout>
  );
}

const BASE =
  process.env.NEXT_PUBLIC_ADMIN_API_BASE || "https://api.coachflow.nz";

async function req(path: string, opts: RequestInit = {}) {
  const res = await fetch(`${BASE}${path}`, {
    ...opts,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(opts.headers || {}),
    },
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

export const api = {
  login: (email: string, secret: string) =>
    req("/admin/login", {
      method: "POST",
      body: JSON.stringify({ email, secret }),
    }),
  me: () => req("/admin/me"),
  tenantsList: () => req("/admin/tenants"),
  createTenant: (name: string) =>
    req(`/admin/tenants?name=${encodeURIComponent(name)}`, { method: "POST" }),
  getRules: (tenantId: string) => req(`/admin/tenants/${tenantId}/rules`),
  setRules: (tenantId: string, yaml_text: string) =>
    req(`/admin/tenants/${tenantId}/rules`, {
      method: "PUT",
      body: JSON.stringify({ yaml_text }),
    }),
  triageDryRun: (tenantId: string, email: any) =>
    req(`/admin/tenants/${tenantId}/triage/dry-run`, {
      method: "POST",
      body: JSON.stringify(email),
    }),
  getConfig: (tenantId: string) => req(`/admin/tenants/${tenantId}/config`),
  setConfig: (tenantId: string, yaml: string) =>
    req(`/admin/tenants/${tenantId}/config`, {
      method: "PUT",
      body: JSON.stringify({ yaml }),
    }),
  validateNotionConfig: (tenantId: string) =>
    req(`/admin/tenants/${tenantId}/notion/validate`, {
      method: "POST",
    }),
  // Approvals & Actions (POC)
  approvals: (filter: string = "all") => req(`/approvals?filter=${encodeURIComponent(filter)}`),
  scan: (domains: string[]) =>
    req(`/actions/scan`, { method: "POST", body: JSON.stringify({ domains }) }),
  approve: (id: string) => req(`/actions/approve/${encodeURIComponent(id)}`, { method: "POST" }),
  edit: (id: string, instructions: string) =>
    req(`/actions/edit/${encodeURIComponent(id)}`, {
      method: "POST",
      body: JSON.stringify({ instructions }),
    }),
  skip: (id: string) => req(`/actions/skip/${encodeURIComponent(id)}`, { method: "POST" }),
};

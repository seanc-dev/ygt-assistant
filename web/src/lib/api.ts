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
  approvals: (filter: string = "all") =>
    req(`/approvals?filter=${encodeURIComponent(filter)}`),
  scan: (domains: string[]) =>
    req(`/actions/scan`, { method: "POST", body: JSON.stringify({ domains }) }),
  approve: (id: string) =>
    req(`/actions/approve/${encodeURIComponent(id)}`, { method: "POST" }),
  edit: (id: string, instructions: string) =>
    req(`/actions/edit/${encodeURIComponent(id)}`, {
      method: "POST",
      body: JSON.stringify({ instructions }),
    }),
  skip: (id: string) =>
    req(`/actions/skip/${encodeURIComponent(id)}`, { method: "POST" }),
  undo: (id: string) =>
    req(`/actions/undo/${encodeURIComponent(id)}`, { method: "POST" }),
  history: (limit = 100) => req(`/history?limit=${limit}`),
  // LucidWork endpoints
  queue: () => req("/api/queue"),
  summaryQueue: (days?: number) =>
    req(`/api/summary/queue${days ? `?days=${days}` : ""}`),
  scheduleToday: () => req("/api/schedule/today"),
  scheduleAlternatives: (body: { existing_events?: any[]; proposed_blocks?: any[] }) =>
    req("/api/schedule/alternatives", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  briefToday: () => req("/api/brief/today"),
  workroomTree: () => req("/api/workroom/tree"),
  createThread: (body: { task_id: string; title: string; prefs?: any }) =>
    req("/api/workroom/thread", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  updateTaskStatus: (taskId: string, status: string) =>
    req(`/api/workroom/task/${encodeURIComponent(taskId)}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    }),
  auditLog: (limit?: number, actionType?: string) =>
    req(`/api/audit/log${limit || actionType ? `?${limit ? `limit=${limit}` : ""}${actionType ? `&action_type=${encodeURIComponent(actionType)}` : ""}` : ""}`),
  settings: () => req("/api/settings"),
  updateSettings: (data: any) =>
    req("/api/settings", { method: "PUT", body: JSON.stringify(data) }),
  statusFlags: () => req("/api/status/flags"),
  // Queue actions
  deferAction: (actionId: string, body: { bucket: string }) =>
    req(`/api/queue/${encodeURIComponent(actionId)}/defer`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  addToToday: (actionId: string, body: { kind: "admin" | "work"; tasks?: string[] }) =>
    req(`/api/queue/${encodeURIComponent(actionId)}/add-to-today`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  replyAction: (actionId: string, body: { draft: string }) =>
    req(`/api/queue/${encodeURIComponent(actionId)}/reply`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
};

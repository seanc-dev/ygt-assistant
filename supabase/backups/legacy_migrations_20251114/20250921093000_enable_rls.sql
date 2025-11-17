-- Enable Row Level Security on all app tables to prevent public access via PostgREST.
-- Our API uses the service role key, which bypasses RLS, so no allow policies are required.

alter table if exists public.tenants enable row level security;

alter table if exists public.tenant_settings enable row level security;

alter table if exists public.connections enable row level security;

alter table if exists public.actions enable row level security;

alter table if exists public.dedupe_keys enable row level security;

alter table if exists public.audit_log enable row level security;

alter table if exists public.rules enable row level security;

alter table if exists public.users enable row level security;

alter table if exists public.client_sessions enable row level security;

-- (Optional) Explicit deny policies for non-service roles. Not strictly necessary since
-- enabling RLS with no policies denies access by default, but kept here for clarity.
do $$
begin
  if not exists (
    select 1 from pg_policies where schemaname = 'public' and tablename = 'users' and policyname = 'deny_all_users'
  ) then
    create policy deny_all_users on public.users for all using (false) with check (false);
  end if;
  if not exists (
    select 1 from pg_policies where schemaname = 'public' and tablename = 'client_sessions' and policyname = 'deny_all_client_sessions'
  ) then
    create policy deny_all_client_sessions on public.client_sessions for all using (false) with check (false);
  end if;
  if not exists (
    select 1 from pg_policies where schemaname = 'public' and tablename = 'tenants' and policyname = 'deny_all_tenants'
  ) then
    create policy deny_all_tenants on public.tenants for all using (false) with check (false);
  end if;
  if not exists (
    select 1 from pg_policies where schemaname = 'public' and tablename = 'tenant_settings' and policyname = 'deny_all_tenant_settings'
  ) then
    create policy deny_all_tenant_settings on public.tenant_settings for all using (false) with check (false);
  end if;
  if not exists (
    select 1 from pg_policies where schemaname = 'public' and tablename = 'connections' and policyname = 'deny_all_connections'
  ) then
    create policy deny_all_connections on public.connections for all using (false) with check (false);
  end if;
  if not exists (
    select 1 from pg_policies where schemaname = 'public' and tablename = 'actions' and policyname = 'deny_all_actions'
  ) then
    create policy deny_all_actions on public.actions for all using (false) with check (false);
  end if;
  if not exists (
    select 1 from pg_policies where schemaname = 'public' and tablename = 'dedupe_keys' and policyname = 'deny_all_dedupe_keys'
  ) then
    create policy deny_all_dedupe_keys on public.dedupe_keys for all using (false) with check (false);
  end if;
  if not exists (
    select 1 from pg_policies where schemaname = 'public' and tablename = 'audit_log' and policyname = 'deny_all_audit_log'
  ) then
    create policy deny_all_audit_log on public.audit_log for all using (false) with check (false);
  end if;
  if not exists (
    select 1 from pg_policies where schemaname = 'public' and tablename = 'rules' and policyname = 'deny_all_rules'
  ) then
    create policy deny_all_rules on public.rules for all using (false) with check (false);
  end if;
end $$;
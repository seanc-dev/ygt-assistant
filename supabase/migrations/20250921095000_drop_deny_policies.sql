-- Remove blanket deny-all policies that can interfere with service_role operations
do $$
begin
  -- Helper to drop if exists
  perform 1;
  -- tenants
  if exists (select 1 from pg_policies where schemaname='public' and tablename='tenants' and policyname='deny_all_tenants') then
    drop policy deny_all_tenants on public.tenants;
  end if;
  -- tenant_settings
  if exists (select 1 from pg_policies where schemaname='public' and tablename='tenant_settings' and policyname='deny_all_tenant_settings') then
    drop policy deny_all_tenant_settings on public.tenant_settings;
  end if;
  -- connections
  if exists (select 1 from pg_policies where schemaname='public' and tablename='connections' and policyname='deny_all_connections') then
    drop policy deny_all_connections on public.connections;
  end if;
  -- users
  if exists (select 1 from pg_policies where schemaname='public' and tablename='users' and policyname='deny_all_users') then
    drop policy deny_all_users on public.users;
  end if;
  -- client_sessions
  if exists (select 1 from pg_policies where schemaname='public' and tablename='client_sessions' and policyname='deny_all_client_sessions') then
    drop policy deny_all_client_sessions on public.client_sessions;
  end if;
  -- actions
  if exists (select 1 from pg_policies where schemaname='public' and tablename='actions' and policyname='deny_all_actions') then
    drop policy deny_all_actions on public.actions;
  end if;
  -- dedupe_keys
  if exists (select 1 from pg_policies where schemaname='public' and tablename='dedupe_keys' and policyname='deny_all_dedupe_keys') then
    drop policy deny_all_dedupe_keys on public.dedupe_keys;
  end if;
  -- audit_log
  if exists (select 1 from pg_policies where schemaname='public' and tablename='audit_log' and policyname='deny_all_audit_log') then
    drop policy deny_all_audit_log on public.audit_log;
  end if;
  -- rules
  if exists (select 1 from pg_policies where schemaname='public' and tablename='rules' and policyname='deny_all_rules') then
    drop policy deny_all_rules on public.rules;
  end if;
end $$;
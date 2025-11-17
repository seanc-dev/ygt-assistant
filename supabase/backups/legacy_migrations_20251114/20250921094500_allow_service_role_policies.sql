-- Allow service_role to bypass RLS via explicit allow policies
do $$
begin
  -- tenants
  if not exists (
    select 1 from pg_policies where schemaname='public' and tablename='tenants' and policyname='allow_service_all_tenants'
  ) then
    create policy allow_service_all_tenants on public.tenants for all to service_role using (true) with check (true);
  end if;

  -- tenant_settings
  if not exists (
    select 1 from pg_policies where schemaname='public' and tablename='tenant_settings' and policyname='allow_service_all_tenant_settings'
  ) then
    create policy allow_service_all_tenant_settings on public.tenant_settings for all to service_role using (true) with check (true);
  end if;

  -- connections
  if not exists (
    select 1 from pg_policies where schemaname='public' and tablename='connections' and policyname='allow_service_all_connections'
  ) then
    create policy allow_service_all_connections on public.connections for all to service_role using (true) with check (true);
  end if;

  -- users
  if not exists (
    select 1 from pg_policies where schemaname='public' and tablename='users' and policyname='allow_service_all_users'
  ) then
    create policy allow_service_all_users on public.users for all to service_role using (true) with check (true);
  end if;

  -- client_sessions
  if not exists (
    select 1 from pg_policies where schemaname='public' and tablename='client_sessions' and policyname='allow_service_all_client_sessions'
  ) then
    create policy allow_service_all_client_sessions on public.client_sessions for all to service_role using (true) with check (true);
  end if;

  -- actions
  if not exists (
    select 1 from pg_policies where schemaname='public' and tablename='actions' and policyname='allow_service_all_actions'
  ) then
    create policy allow_service_all_actions on public.actions for all to service_role using (true) with check (true);
  end if;

  -- dedupe_keys
  if not exists (
    select 1 from pg_policies where schemaname='public' and tablename='dedupe_keys' and policyname='allow_service_all_dedupe_keys'
  ) then
    create policy allow_service_all_dedupe_keys on public.dedupe_keys for all to service_role using (true) with check (true);
  end if;

  -- audit_log
  if not exists (
    select 1 from pg_policies where schemaname='public' and tablename='audit_log' and policyname='allow_service_all_audit_log'
  ) then
    create policy allow_service_all_audit_log on public.audit_log for all to service_role using (true) with check (true);
  end if;

  -- rules
  if not exists (
    select 1 from pg_policies where schemaname='public' and tablename='rules' and policyname='allow_service_all_rules'
  ) then
    create policy allow_service_all_rules on public.rules for all to service_role using (true) with check (true);
  end if;
end $$;
-- Row Level Security policies and helper functions

create schema if not exists auth_helpers;

create or replace function auth_helpers.current_tenant_id()
returns uuid
language plpgsql
stable
as $$
declare
  v_claim text;
begin
  v_claim := current_setting('request.jwt.claim.tenant_id', true);
  if v_claim is null or v_claim = '' then
    return null;
  end if;
  return v_claim::uuid;
exception
  when others then
    return null;
end;
$$;

create or replace function auth_helpers.is_service_role()
returns boolean
language sql
stable
as $$
  select coalesce(current_setting('request.jwt.claim.role', true), '') = 'service_role';
$$;

create or replace function auth_helpers.tenant_matches(target_tenant uuid)
returns boolean
language sql
stable
as $$
  select auth_helpers.is_service_role()
         or (target_tenant is not null and target_tenant = auth_helpers.current_tenant_id());
$$;

-- Helper macro to reduce repetition via DO block
do $$
declare
  table_name text;
  tables text[] := array[
    'users',
    'connections_ms',
    'projects',
    'tasks',
    'threads',
    'messages',
    'schedule_blocks',
    'action_items',
    'docs',
    'doc_events',
    'core_memory_items',
    'audit_log',
    'usage_daily',
    'billing_subscriptions',
    'billing_seats'
  ];
begin
  foreach table_name in array tables loop
    execute format('alter table %I enable row level security;', table_name);

    execute format(
      'create policy %I_select on %I for select using (auth_helpers.tenant_matches(tenant_id));',
      table_name, table_name
    );

    execute format(
      'create policy %I_insert on %I for insert with check (auth_helpers.tenant_matches(tenant_id));',
      table_name, table_name
    );

    execute format(
      'create policy %I_update on %I for update using (auth_helpers.tenant_matches(tenant_id)) with check (auth_helpers.tenant_matches(tenant_id));',
      table_name, table_name
    );

    execute format(
      'create policy %I_delete on %I for delete using (auth_helpers.tenant_matches(tenant_id));',
      table_name, table_name
    );
  end loop;
end $$;

-- Tenants table policies (special-case id instead of tenant_id column)
alter table tenants enable row level security;

create policy tenants_select_self on tenants for
select using (
        auth_helpers.is_service_role ()
        or id = auth_helpers.current_tenant_id ()
    );

create policy tenants_mutate_service on tenants for all using (
    auth_helpers.is_service_role ()
)
with
    check (
        auth_helpers.is_service_role ()
    );

-- updated_at helper
create or replace function auth_helpers.touch_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

-- register triggers for tables with updated_at columns
do $$
declare
  table_name text;
  tables text[] := array[
    'tenants',
    'users',
    'connections_ms',
    'projects',
    'tasks',
    'threads',
    'schedule_blocks',
    'action_items',
    'docs',
    'core_memory_items',
    'billing_subscriptions'
  ];
begin
  foreach table_name in array tables loop
    execute format(
      'drop trigger if exists %I_touch_updated_at on %I;',
      table_name, table_name
    );

    execute format(
      'create trigger %I_touch_updated_at before update on %I for each row execute function auth_helpers.touch_updated_at();',
      table_name, table_name
    );
  end loop;
end $$;

-- thread last_message_at maintenance
create or replace function auth_helpers.bump_thread_last_message()
returns trigger
language plpgsql
as $$
begin
  update threads
     set last_message_at = coalesce(new.created_at, now()),
         updated_at = now()
   where id = new.thread_id;
  return new;
end;
$$;

drop trigger if exists messages_touch_thread on messages;

create trigger messages_touch_thread
  after insert on messages
  for each row
  execute function auth_helpers.bump_thread_last_message();
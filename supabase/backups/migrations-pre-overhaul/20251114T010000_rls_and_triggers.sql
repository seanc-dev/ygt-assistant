-- RLS policies, helper functions, and timestamp triggers

-- Helper to fetch tenant id from JWT claims (defaults to NULL)
create or replace function public.current_tenant_id()
returns uuid
language plpgsql
stable
security definer
set search_path = public
as $$
declare
  claims jsonb;
  tenant text;
begin
  begin
    claims := nullif(current_setting('request.jwt.claims', true), '')::jsonb;
  exception
    when others then
      return null;
  end;

  if claims ? 'tenant_id' then
    tenant := claims->>'tenant_id';
    if tenant is not null and tenant <> '' then
      return tenant::uuid;
    end if;
  end if;

  return null;
end;
$$;

grant execute on function public.current_tenant_id() to anon, authenticated, service_role;

-- Generic updated_at trigger
create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

-- Trigger to bump thread timestamps when new messages arrive
create or replace function public.bump_thread_last_message()
returns trigger
language plpgsql
as $$
begin
  update threads
     set last_message_at = new.created_at,
         updated_at = now()
   where id = new.thread_id;
  return new;
end;
$$;

-- Attach updated_at triggers
create trigger set_updated_at_on_tenants before update on tenants
  for each row execute function public.set_updated_at();

create trigger set_updated_at_on_users before update on users
  for each row execute function public.set_updated_at();

create trigger set_updated_at_on_connections before update on connections_ms
  for each row execute function public.set_updated_at();

create trigger set_updated_at_on_projects before update on projects
  for each row execute function public.set_updated_at();

create trigger set_updated_at_on_tasks before update on tasks
  for each row execute function public.set_updated_at();

create trigger set_updated_at_on_threads before update on threads
  for each row execute function public.set_updated_at();

create trigger set_updated_at_on_schedule_blocks before update on schedule_blocks
  for each row execute function public.set_updated_at();

create trigger set_updated_at_on_action_items before update on action_items
  for each row execute function public.set_updated_at();

create trigger set_updated_at_on_docs before update on docs
  for each row execute function public.set_updated_at();

create trigger set_updated_at_on_core_memory before update on core_memory_items
  for each row execute function public.set_updated_at();

create trigger set_updated_at_on_billing_subscriptions before update on billing_subscriptions
  for each row execute function public.set_updated_at();

-- Thread timestamp trigger
create trigger messages_bump_thread after insert on messages
  for each row execute function public.bump_thread_last_message();

-- Helper expression for policies
create or replace function public.tenant_matches(_tenant uuid)
returns boolean
language sql
immutable
as $$
select case
  when auth.role() = 'service_role' then true
  else coalesce(_tenant = public.current_tenant_id(), false)
end;
$$;

grant execute on function public.tenant_matches(uuid) to anon, authenticated, service_role;

-- Enable row level security & policies
alter table tenants enable row level security;
create policy tenants_select on tenants
  for select using (public.tenant_matches(id));
create policy tenants_write on tenants
  for all using (public.tenant_matches(id))
  with check (public.tenant_matches(id));

alter table users enable row level security;
create policy users_select on users
  for select using (public.tenant_matches(tenant_id));
create policy users_write on users
  for all using (public.tenant_matches(tenant_id))
  with check (public.tenant_matches(tenant_id));

alter table connections_ms enable row level security;
create policy connections_select on connections_ms
  for select using (public.tenant_matches(tenant_id));
create policy connections_write on connections_ms
  for all using (public.tenant_matches(tenant_id))
  with check (public.tenant_matches(tenant_id));

alter table projects enable row level security;
create policy projects_select on projects
  for select using (public.tenant_matches(tenant_id));
create policy projects_write on projects
  for all using (public.tenant_matches(tenant_id))
  with check (public.tenant_matches(tenant_id));

alter table tasks enable row level security;
create policy tasks_select on tasks
  for select using (public.tenant_matches(tenant_id));
create policy tasks_write on tasks
  for all using (public.tenant_matches(tenant_id))
  with check (public.tenant_matches(tenant_id));

alter table threads enable row level security;
create policy threads_select on threads
  for select using (public.tenant_matches(tenant_id));
create policy threads_write on threads
  for all using (public.tenant_matches(tenant_id))
  with check (public.tenant_matches(tenant_id));

alter table messages enable row level security;
create policy messages_select on messages
  for select using (public.tenant_matches(tenant_id));
create policy messages_write on messages
  for all using (public.tenant_matches(tenant_id))
  with check (public.tenant_matches(tenant_id));

alter table schedule_blocks enable row level security;
create policy schedule_blocks_select on schedule_blocks
  for select using (public.tenant_matches(tenant_id));
create policy schedule_blocks_write on schedule_blocks
  for all using (public.tenant_matches(tenant_id))
  with check (public.tenant_matches(tenant_id));

alter table action_items enable row level security;
create policy action_items_select on action_items
  for select using (public.tenant_matches(tenant_id));
create policy action_items_write on action_items
  for all using (public.tenant_matches(tenant_id))
  with check (public.tenant_matches(tenant_id));

alter table docs enable row level security;
create policy docs_select on docs
  for select using (public.tenant_matches(tenant_id));
create policy docs_write on docs
  for all using (public.tenant_matches(tenant_id))
  with check (public.tenant_matches(tenant_id));

alter table doc_events enable row level security;
create policy doc_events_select on doc_events
  for select using (public.tenant_matches(tenant_id));
create policy doc_events_write on doc_events
  for all using (public.tenant_matches(tenant_id))
  with check (public.tenant_matches(tenant_id));

alter table core_memory_items enable row level security;
create policy core_memory_select on core_memory_items
  for select using (public.tenant_matches(tenant_id));
create policy core_memory_write on core_memory_items
  for all using (public.tenant_matches(tenant_id))
  with check (public.tenant_matches(tenant_id));

alter table audit_log enable row level security;
create policy audit_log_select on audit_log
  for select using (public.tenant_matches(tenant_id));
create policy audit_log_write on audit_log
  for all using (public.tenant_matches(tenant_id))
  with check (public.tenant_matches(tenant_id));

alter table usage_daily enable row level security;
create policy usage_daily_select on usage_daily
  for select using (public.tenant_matches(tenant_id));
create policy usage_daily_write on usage_daily
  for all using (public.tenant_matches(tenant_id))
  with check (public.tenant_matches(tenant_id));

alter table billing_subscriptions enable row level security;
create policy billing_subscriptions_select on billing_subscriptions
  for select using (public.tenant_matches(tenant_id));
create policy billing_subscriptions_write on billing_subscriptions
  for all using (public.tenant_matches(tenant_id))
  with check (public.tenant_matches(tenant_id));

alter table billing_seats enable row level security;
create policy billing_seats_select on billing_seats
  for select using (public.tenant_matches(tenant_id));
create policy billing_seats_write on billing_seats
  for all using (public.tenant_matches(tenant_id))
  with check (public.tenant_matches(tenant_id));


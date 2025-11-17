-- Baseline multi-tenant schema for LucidWork / YGT Assistant
create extension if not exists "pgcrypto";
create extension if not exists "uuid-ossp";
create extension if not exists "vector";

-- 0) ENUMS / TYPES
create type role_type as enum ('admin', 'member');
create type user_status as enum ('invited', 'active', 'suspended', 'deleted');
create type tenant_status as enum ('trial', 'active', 'paused', 'closed');
create type billing_source as enum ('ms_marketplace', 'direct');
create type task_status as enum ('backlog', 'ready', 'doing', 'blocked', 'done', 'todo');
create type priority_level as enum ('low', 'medium', 'high', 'urgent');
create type action_state as enum ('queued', 'deferred', 'completed', 'dismissed', 'converted_to_task');
create type action_source as enum ('email', 'teams', 'doc', 'calendar', 'manual');
create type schedule_block_kind as enum ('focus', 'admin', 'meeting', 'break', 'travel', 'buffer');
create type schedule_block_source as enum ('assistant', 'user');
create type memory_level as enum ('episodic', 'semantic', 'procedural', 'narrative');
create type message_role as enum ('user', 'assistant', 'system');
create type subscription_status as enum ('trialing', 'active', 'past_due', 'canceled');

-- 1) TENANCY & USERS
create table tenants (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  name text not null,
  ms_tenant_id text unique,
  status tenant_status not null default 'trial',
  billing_plan text not null default 'starter',
  seat_limit integer,
  trial_ends_at timestamptz,
  subscription_ends_at timestamptz,
  marketplace_listing_id text,
  metadata jsonb not null default '{}'::jsonb
);

create table users (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  tenant_id uuid not null references tenants(id) on delete cascade,
  email text not null,
  display_name text,
  role role_type not null default 'member',
  status user_status not null default 'invited',
  ms_user_id text,
  locale text default 'en',
  time_zone text default 'UTC',
  workday_start time default '09:00',
  workday_end time default '17:00',
  preferences jsonb not null default '{}'::jsonb
);

create unique index users_tenant_email_idx on users(tenant_id, lower(email));

-- 2) GRAPH / PROVIDER CONNECTIONS
create table connections_ms (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  tenant_id uuid not null references tenants(id) on delete cascade,
  user_id uuid references users(id) on delete cascade,
  provider text not null default 'microsoft_graph',
  scopes text[] not null,
  access_token_enc bytea not null,
  refresh_token_enc bytea,
  expires_at timestamptz,
  ms_account_id text,
  status text not null default 'active',
  last_error text,
  unique (tenant_id, user_id, provider)
);

-- 3) PROJECTS / TASKS / WORKROOM
create table projects (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  tenant_id uuid not null references tenants(id) on delete cascade,
  owner_id uuid references users(id),
  name text not null,
  description text,
  status text not null default 'active',
  priority priority_level default 'medium',
  order_index integer default 0,
  metadata jsonb not null default '{}'::jsonb
);

create index projects_tenant_idx on projects(tenant_id);

create table tasks (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  tenant_id uuid not null references tenants(id) on delete cascade,
  project_id uuid references projects(id) on delete set null,
  owner_id uuid references users(id),
  title text not null,
  description text,
  status task_status not null default 'backlog',
  priority priority_level default 'medium',
  due_at timestamptz,
  order_index integer default 0,
  source_type action_source default 'manual',
  source_ref jsonb not null default '{}'::jsonb
);

create index tasks_tenant_project_idx on tasks(tenant_id, project_id);

-- 4) THREADS + MESSAGES
create table threads (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  tenant_id uuid not null references tenants(id) on delete cascade,
  task_id uuid references tasks(id) on delete set null,
  source_action_id uuid,
  title text,
  created_by uuid references users(id),
  last_message_at timestamptz,
  status text not null default 'open',
  unique (tenant_id, source_action_id)
);

create index threads_tenant_task_idx on threads(tenant_id, task_id);

create table messages (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  tenant_id uuid not null references tenants(id) on delete cascade,
  thread_id uuid not null references threads(id) on delete cascade,
  user_id uuid references users(id),
  role message_role not null,
  content text not null,
  tokens_in integer default 0,
  tokens_out integer default 0,
  metadata jsonb not null default '{}'::jsonb
);

create index messages_thread_idx on messages(thread_id, created_at);

-- 6) SCHEDULE BLOCKS
create table schedule_blocks (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  tenant_id uuid not null references tenants(id) on delete cascade,
  user_id uuid not null references users(id) on delete cascade,
  day date not null,
  start_at timestamptz not null,
  end_at timestamptz not null,
  kind schedule_block_kind not null,
  source schedule_block_source not null,
  ms_event_id text,
  status text not null default 'planned',
  metadata jsonb not null default '{}'::jsonb
);

create index schedule_blocks_user_day_idx on schedule_blocks(tenant_id, user_id, day);

-- 5) ACTION QUEUE / DEFER / SCHEDULE LINK
create table action_items (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  tenant_id uuid not null references tenants(id) on delete cascade,
  owner_id uuid not null references users(id) on delete cascade,
  source_type action_source not null,
  source_id text,
  priority priority_level default 'medium',
  state action_state not null default 'queued',
  due_at timestamptz,
  defer_until timestamptz,
  added_to_today boolean not null default false,
  schedule_block_id uuid references schedule_blocks(id) deferrable initially deferred,
  thread_id uuid references threads(id),
  dedupe_key text,
  payload jsonb not null default '{}'::jsonb
);

create unique index action_items_dedupe_idx
  on action_items(tenant_id, owner_id, source_type, dedupe_key)
  where dedupe_key is not null;

create index action_items_queue_idx
  on action_items(tenant_id, owner_id, state, priority, defer_until);

-- 7) DOCS + CHANGE SUMMARIES
create table docs (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  tenant_id uuid not null references tenants(id) on delete cascade,
  drive_id text,
  item_id text,
  name text not null,
  url text,
  is_followed boolean not null default true,
  last_change_token text,
  last_seen_at timestamptz
);

create unique index docs_drive_item_idx on docs(tenant_id, drive_id, item_id);

create table doc_events (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  tenant_id uuid not null references tenants(id) on delete cascade,
  doc_id uuid not null references docs(id) on delete cascade,
  event_type text not null,
  happened_at timestamptz not null,
  summary text,
  payload jsonb not null default '{}'::jsonb,
  surfaced_action_id uuid references action_items(id)
);

create index doc_events_doc_idx on doc_events(doc_id, happened_at);

-- 8) CORE MEMORY (pgvector)
create table core_memory_items (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  tenant_id uuid not null references tenants(id) on delete cascade,
  user_id uuid references users(id) on delete set null,
  level memory_level not null,
  content text not null,
  embedding vector(1536),
  metadata jsonb not null default '{}'::jsonb,
  last_accessed_at timestamptz,
  expires_at timestamptz
);

create index core_memory_tenant_level_idx on core_memory_items(tenant_id, level);
create index core_memory_embedding_idx on core_memory_items using ivfflat (embedding vector_cosine_ops);

-- 9) AUDIT / USAGE
create table audit_log (
  id bigserial primary key,
  created_at timestamptz not null default now(),
  tenant_id uuid not null references tenants(id) on delete cascade,
  user_id uuid references users(id),
  action_type text not null,
  target_type text,
  target_id text,
  request_id text,
  payload jsonb not null default '{}'::jsonb
);

create index audit_tenant_ts_idx on audit_log(tenant_id, created_at);

create table usage_daily (
  tenant_id uuid not null references tenants(id) on delete cascade,
  day date not null,
  user_id uuid references users(id),
  tokens_input bigint not null default 0,
  tokens_output bigint not null default 0,
  actions_count integer not null default 0,
  messages_count integer not null default 0,
  schedule_plans integer not null default 0,
  primary key (tenant_id, day, user_id)
);

-- 10) BILLING & SUBSCRIPTIONS
create table billing_subscriptions (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  tenant_id uuid not null references tenants(id) on delete cascade,
  source billing_source not null,
  external_customer_id text,
  external_subscription_id text,
  plan_code text not null,
  seat_count integer not null default 0,
  status subscription_status not null default 'trialing',
  started_at timestamptz not null default now(),
  current_period_end timestamptz,
  canceled_at timestamptz,
  metadata jsonb not null default '{}'::jsonb
);

create table billing_seats (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  subscription_id uuid not null references billing_subscriptions(id) on delete cascade,
  tenant_id uuid not null references tenants(id) on delete cascade,
  user_id uuid references users(id),
  ms_user_id text,
  active boolean not null default true,
  unique (subscription_id, user_id)
);


-- LLM Ops Protocol: task_sources and task_action_links tables
-- Adds source tracking and many-to-many linking between tasks and actions

-- Add task_id to action_items for primary task link
alter table action_items
  add column if not exists task_id uuid references tasks(id) on delete set null;

create index if not exists action_items_task_idx on action_items (tenant_id, task_id);

-- task_sources: many-to-many between tasks and underlying sources (including action linkage)
create table if not exists task_sources (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  tenant_id uuid not null references tenants(id) on delete cascade,
  task_id uuid not null references tasks(id) on delete cascade,
  source_type action_source not null,
  source_id text,
  doc_id uuid references docs(id) on delete set null,
  action_id uuid references action_items(id) on delete cascade,
  metadata jsonb not null default '{}'::jsonb
);

create index if not exists task_sources_tenant_task_idx on task_sources (tenant_id, task_id);
create index if not exists task_sources_source_idx on task_sources (tenant_id, source_type, source_id);

-- task_action_links: many-to-many between tasks and actions (for future multi-select support)
create table if not exists task_action_links (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  tenant_id uuid not null references tenants(id) on delete cascade,
  task_id uuid not null references tasks(id) on delete cascade,
  action_id uuid not null references action_items(id) on delete cascade,
  metadata jsonb not null default '{}'::jsonb,
  unique (tenant_id, task_id, action_id)
);

create index if not exists task_action_links_task_idx on task_action_links (tenant_id, task_id);
create index if not exists task_action_links_action_idx on task_action_links (tenant_id, action_id);


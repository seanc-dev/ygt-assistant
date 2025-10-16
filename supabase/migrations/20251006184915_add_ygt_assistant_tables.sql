-- YGT Assistant POC tables (idempotent). Reuses existing audit_log.
create extension if not exists vector;

create table if not exists approvals (
  id uuid primary key default gen_random_uuid(),
  kind text,
  source text,
  title text,
  summary text,
  payload jsonb,
  risk text,
  status text,
  expires_at timestamptz,
  created_at timestamptz default now()
);

create index if not exists idx_approvals_status_expires on approvals (status, expires_at);

create table if not exists drafts (
  id uuid primary key default gen_random_uuid(),
  recipients jsonb,
  subject text,
  body text,
  tone text,
  status text,
  risk text,
  created_at timestamptz default now()
);

create index if not exists idx_drafts_status on drafts (status);

create table if not exists automations (
  id uuid primary key default gen_random_uuid(),
  trigger jsonb,
  conditions jsonb,
  action jsonb,
  enabled boolean default false,
  created_at timestamptz default now()
);

create index if not exists idx_automations_enabled on automations (enabled);

create table if not exists core_memory (
  id uuid primary key default gen_random_uuid(),
  level text,
  key text,
  value jsonb,
  vector vector(1536),
  meta jsonb,
  created_at timestamptz default now(),
  last_used_at timestamptz
);

-- Conditionally create ivfflat index only if vector extension and table exist. Errors ignored in idempotent context.
-- Note: requires pgvector >= 0.5.0 and populated vectors to create ivfflat; safe to skip in dev.
do $$
begin
  perform 1 from pg_extension where extname = 'vector';
  if found then
    execute 'create index if not exists idx_core_memory_vector on core_memory using ivfflat (vector)';
  end if;
end$$;

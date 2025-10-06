create extension if not exists vector;

create table if not exists tenants (
    id uuid primary key default gen_random_uuid (),
    name text not null
);

create table if not exists connections (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid references tenants(id) on delete cascade,
  provider text not null,
  access_token_encrypted text not null,
  refresh_token_encrypted text,
  meta jsonb default '{}'::jsonb,
  created_at timestamptz default now()
);

create table if not exists actions (
    id uuid primary key default gen_random_uuid (),
    tenant_id uuid references tenants (id) on delete cascade,
    type text not null,
    payload_json jsonb not null,
    status text default 'planned',
    request_id text,
    created_at timestamptz default now()
);

create table if not exists dedupe_keys (
    tenant_id uuid references tenants (id) on delete cascade,
    external_id text not null,
    kind text not null,
    action_id uuid references actions (id) on delete cascade,
    primary key (tenant_id, external_id, kind)
);

create table if not exists audit_log (
    request_id text primary key,
    tenant_id uuid,
    dry_run boolean default true,
    actions jsonb not null,
    results jsonb not null,
    created_at timestamptz default now()
);

create table if not exists rules (
    tenant_id uuid references tenants (id) on delete cascade,
    yaml text not null,
    version int default 1,
    updated_at timestamptz default now(),
    primary key (tenant_id)
);

-- Sprint 8: tenant settings
create table if not exists tenant_settings (
    tenant_id uuid references tenants (id) on delete cascade,
    key text not null,
    value text not null,
    updated_at timestamptz default now(),
    primary key (tenant_id, key)
);
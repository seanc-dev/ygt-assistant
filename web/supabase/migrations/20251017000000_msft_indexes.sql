-- Ensure oauth_tokens and profiles shapes + indexes (idempotent)
create table if not exists oauth_tokens (
  user_id text primary key,
  tenant_id text,
  provider text not null,
  access_token text not null,
  refresh_token text not null,
  expiry timestamptz not null,
  scopes text[] not null,
  created_at timestamptz default now()
);

create table if not exists profiles (
  id uuid primary key default gen_random_uuid(),
  aad_user_id text unique,
  email text,
  display_name text,
  locale text,
  tz text
);

create index if not exists idx_oauth_tokens_provider_tenant on oauth_tokens(provider, tenant_id);
create index if not exists idx_audit_ts on audit(ts);

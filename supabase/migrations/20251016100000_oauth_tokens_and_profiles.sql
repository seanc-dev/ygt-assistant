-- OAuth tokens and profiles for Google integrations
-- Idempotent guards
create extension if not exists pgcrypto;

create table if not exists oauth_tokens (
  user_id text primary key,
  provider text not null,
  access_token text not null,
  refresh_token text not null,
  expiry timestamptz not null,
  scopes text[] not null,
  created_at timestamptz default now()
);

create table if not exists profiles (
    id uuid primary key default gen_random_uuid (),
    whatsapp_user_id text unique,
    google_user_id text unique,
    locale text,
    tz text
);

-- Minimal indexes
create index if not exists idx_oauth_tokens_provider on oauth_tokens (provider);

create index if not exists idx_profiles_whatsapp_user_id on profiles (whatsapp_user_id);
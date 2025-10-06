create table if not exists users (
    id uuid primary key default gen_random_uuid (),
    tenant_id uuid references tenants (id) on delete cascade,
    email text not null unique,
    name text,
    password_hash text not null,
    must_change_password boolean not null default true,
    created_at timestamptz default now()
);

create table if not exists client_sessions (
    token text primary key,
    user_id uuid references users (id) on delete cascade,
    created_at timestamptz default now(),
    expires_at timestamptz
);
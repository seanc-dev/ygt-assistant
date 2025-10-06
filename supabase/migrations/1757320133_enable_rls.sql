-- enable row level security on core tables
alter table if exists tenants enable row level security;
alter table if exists connections enable row level security;
alter table if exists actions enable row level security;
alter table if exists dedupe_keys enable row level security;
alter table if exists audit_log enable row level security;
alter table if exists rules enable row level security;
alter table if exists tenant_settings enable row level security;

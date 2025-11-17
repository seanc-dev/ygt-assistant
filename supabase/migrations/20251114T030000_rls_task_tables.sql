-- RLS policies for task_sources and task_action_links tables

-- Enable RLS on new tables
alter table task_sources enable row level security;

alter table task_action_links enable row level security;

-- RLS policies for task_sources
create policy task_sources_select on task_sources for
select using (
        auth_helpers.tenant_matches (tenant_id)
    );

create policy task_sources_insert on task_sources for
insert
with
    check (
        auth_helpers.tenant_matches (tenant_id)
    );

create policy task_sources_update on task_sources for
update using (
    auth_helpers.tenant_matches (tenant_id)
)
with
    check (
        auth_helpers.tenant_matches (tenant_id)
    );

create policy task_sources_delete on task_sources for delete using (
    auth_helpers.tenant_matches (tenant_id)
);

-- RLS policies for task_action_links
create policy task_action_links_select on task_action_links for
select using (
        auth_helpers.tenant_matches (tenant_id)
    );

create policy task_action_links_insert on task_action_links for
insert
with
    check (
        auth_helpers.tenant_matches (tenant_id)
    );

create policy task_action_links_update on task_action_links for
update using (
    auth_helpers.tenant_matches (tenant_id)
)
with
    check (
        auth_helpers.tenant_matches (tenant_id)
    );

create policy task_action_links_delete on task_action_links for delete using (
    auth_helpers.tenant_matches (tenant_id)
);
-- Add deleted_at fields for soft deletion of projects and tasks
-- Migration: 20250115000000_add_deleted_at_fields.sql

-- Add deleted_at to projects table
alter table projects
  add column if not exists deleted_at timestamptz;

-- Add deleted_at to tasks table
alter table tasks
  add column if not exists deleted_at timestamptz;

-- Create indexes for filtering deleted items
create index if not exists projects_deleted_at_idx on projects (deleted_at)
  where deleted_at is null;

create index if not exists tasks_deleted_at_idx on tasks (deleted_at)
  where deleted_at is null;

-- Add index for cascade queries (finding tasks by project_id when deleting)
create index if not exists tasks_project_deleted_idx on tasks (project_id, deleted_at)
  where deleted_at is null;


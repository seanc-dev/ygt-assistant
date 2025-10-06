-- Move pgvector extension objects out of public schema
create schema if not exists extensions;
-- If already installed in public and relocatable, move it
do $$ begin if exists (
    select 1
    from
        pg_extension e
        join pg_namespace n on n.oid = e.extnamespace
    where
        e.extname = 'vector'
        and n.nspname = 'public'
) then
alter extension vector
set
    schema extensions;

end if;

end $$;

-- Ensure extension exists in extensions schema for fresh setups
create extension if not exists vector
with
    schema extensions;
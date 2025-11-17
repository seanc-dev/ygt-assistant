# Supabase Workflow

## Prerequisites

- Supabase CLI ≥ v2.58 installed and logged in (`supabase login` + `supabase projects list`).
- Project ref: `ympffwpecionqhaloufr` (already stored in `.env.local`).
- Service role key stored in `SUPABASE_API_SECRET`.
- Web clients need `NEXT_PUBLIC_SUPABASE_URL` + `NEXT_PUBLIC_SUPABASE_ANON_KEY` populated for any future direct Supabase access.

## Common Commands

```bash
# Link (only needed once per environment)
supabase link --project-ref ympffwpecionqhaloufr

# Start/stop local stack
supabase start
supabase stop

# Reset local stack (drops data, reapplies migrations, runs seeds)
supabase db reset

# Lint migrations before committing
supabase db lint

# Deploy latest migrations + seeds to the linked project
supabase db push

# Dump remote schema snapshot before destructive changes
mkdir -p supabase/backups
supabase db dump --schema public --file supabase/backups/$(date +%Y%m%d)_pre_overhaul.sql
```

## Seeds

- Developer fixtures live in `supabase/seed.sql`.
- `supabase db reset` automatically executes the seed file after migrations.
- The seed creates:
  - One tenant/user pair (`demo.user@example.com`).
  - Sample project/task/thread/messages.
  - Representative schedule blocks, action items, docs, billing rows.

## Backup Strategy

1. Dump the remote schema before destructive changes (see command above).
2. Archive previous migrations under `supabase/backups/`.

## Rolling Out Changes

1. Author new migrations in `supabase/migrations/`.
2. Apply locally with `supabase db reset`; fix any errors.
3. Run automated tests touching the repositories.
4. Push to remote via `supabase db push`.
5. Update application secrets:
   - `SUPABASE_URL`
   - `SUPABASE_API_SECRET`
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`

## Notes

- RLS is enabled on every tenant-scoped table. Queries must include a valid `tenant_id` claim in their JWT unless they run with the service role key.
- Helper functions live under the `auth_helpers` schema (`current_tenant_id`, `tenant_matches`, `touch_updated_at`, `bump_thread_last_message`). They are safe to reuse in future policies or triggers.

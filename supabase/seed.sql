-- Seed data for local development of the LucidWork workroom stack
do $$
declare
  v_tenant_id uuid;
  v_user_id uuid;
  v_project_id uuid;
  v_task_id uuid;
  v_thread_id uuid;
  v_schedule_id uuid;
  v_action_id uuid;
  v_doc_id uuid;
  v_subscription_id uuid;
begin
  insert into tenants (name, status, billing_plan, seat_limit, metadata)
  values (
    'Demo Tenant',
    'active',
    'starter',
    25,
    '{"seed": true, "segment": "demo"}'::jsonb
  )
  returning id into v_tenant_id;

  insert into users (tenant_id, email, display_name, role, status, time_zone, preferences)
  values (v_tenant_id, 'test.user+local@example.com', 'Demo User', 'admin', 'active', 'UTC', '{"focus_mode": "workroom"}'::jsonb)
  returning id into v_user_id;

  insert into connections_ms (
    tenant_id,
    user_id,
    scopes,
    access_token_enc,
    refresh_token_enc,
    expires_at,
    ms_account_id,
    status,
    last_error
  )
  values (
    v_tenant_id,
    v_user_id,
    array['User.Read', 'Mail.Read'],
    convert_to('demo-access-token', 'utf8'),
    convert_to('demo-refresh-token', 'utf8'),
    now() + interval '1 day',
    'demo.user@example.com',
    'active',
    null
  );

  insert into projects (tenant_id, owner_id, name, description, priority, metadata)
  values (v_tenant_id, v_user_id, 'Launch Readiness', 'Prep work for LucidWork beta launch', 'high', '{"color":"blue"}'::jsonb)
  returning id into v_project_id;

  insert into tasks (tenant_id, project_id, owner_id, title, description, status, priority, due_at, source_type)
  values (
    v_tenant_id,
    v_project_id,
    v_user_id,
    'Finalize onboarding flow',
    'Tighten copy and task doc before rollout.',
    'doing',
    'urgent',
    now() + interval '5 days',
    'manual'
  )
  returning id into v_task_id;

  insert into threads (tenant_id, task_id, title, created_by, status)
  values (v_tenant_id, v_task_id, 'Inline chat polish', v_user_id, 'open')
  returning id into v_thread_id;

  insert into messages (tenant_id, thread_id, user_id, role, content)
  values
    (v_tenant_id, v_thread_id, v_user_id, 'user', 'Can you summarize the outstanding UI fixes before tomorrow''s review?'),
    (v_tenant_id, v_thread_id, null, 'assistant', 'Sure — outstanding items: nav clickaway cleanup, Supabase schema hardening, and scroll polish. Need anything else?');

  insert into schedule_blocks (tenant_id, user_id, day, start_at, end_at, kind, source, metadata)
  values (
    v_tenant_id,
    v_user_id,
    current_date,
    date_trunc('day', now()) + interval '13 hours',
    date_trunc('day', now()) + interval '15 hours',
    'focus',
    'assistant',
    '{"label":"Ship chat polish"}'::jsonb
  )
  returning id into v_schedule_id;

  insert into action_items (tenant_id, owner_id, source_type, source_id, priority, state, due_at, schedule_block_id, thread_id, dedupe_key, payload)
  values (
    v_tenant_id,
    v_user_id,
    'email',
    'msg-001',
    'high',
    'queued',
    now() + interval '1 day',
    v_schedule_id,
    v_thread_id,
    'demo-inline-chat',
    '{"preview":"Finalize inline chat polish","category":"needs_response"}'::jsonb
  )
  returning id into v_action_id;

  insert into docs (tenant_id, drive_id, item_id, name, url, is_followed, last_change_token, last_seen_at)
  values (
    v_tenant_id,
    'drive-placeholder',
    'doc-001',
    'Launch Checklist',
    'https://example.com/doc/launch',
    true,
    'change-token',
    now()
  )
  returning id into v_doc_id;

  insert into doc_events (tenant_id, doc_id, event_type, happened_at, summary, payload, surfaced_action_id)
  values (
    v_tenant_id,
    v_doc_id,
    'modified',
    now() - interval '1 hour',
    'Updated checklist with chat tasks',
    '{"author":"Demo User"}'::jsonb,
    v_action_id
  );

  insert into core_memory_items (tenant_id, user_id, level, content, metadata)
  values (
    v_tenant_id,
    v_user_id,
    'semantic',
    'Demo tenant prefers chat-first workflows with inline approvals.',
    '{"origin":"seed"}'::jsonb
  );

  insert into billing_subscriptions (tenant_id, source, plan_code, seat_count, status, current_period_end, metadata)
  values (
    v_tenant_id,
    'direct',
    'starter',
    10,
    'active',
    now() + interval '30 days',
    '{"seed":true}'::jsonb
  )
  returning id into v_subscription_id;

  insert into billing_seats (subscription_id, tenant_id, user_id, ms_user_id, active)
  values (
    v_subscription_id,
    v_tenant_id,
    v_user_id,
    'seed-ms-user',
    true
  );

  insert into usage_daily (tenant_id, day, user_id, tokens_input, tokens_output, actions_count, messages_count, schedule_plans)
  values (
    v_tenant_id,
    current_date,
    v_user_id,
    1200,
    800,
    3,
    4,
    1
  )
  on conflict (tenant_id, day, user_id) do update
    set tokens_input = excluded.tokens_input,
        tokens_output = excluded.tokens_output,
        actions_count = excluded.actions_count,
        messages_count = excluded.messages_count,
        schedule_plans = excluded.schedule_plans;

  insert into audit_log (tenant_id, user_id, action_type, target_type, target_id, request_id, payload)
  values (
    v_tenant_id,
    v_user_id,
    'seed.init',
    'tenant',
    v_tenant_id::text,
    'seed-request',
    '{"note":"Seeded baseline data"}'::jsonb
  );
end;
$$;
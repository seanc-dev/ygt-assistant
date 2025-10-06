# Sprint 8 – Admin automation, tenant settings, invite links

- SettingsRepo (per-tenant key/values)
- Connect redirect flow
- Admin endpoints: settings get/put, invite
- Notion adapters use tenant settings
- Admin UI: Setup page (settings + invite)

Test Outline:
1) Connect Redirect
  - redirects to provider with state param
2) Settings & Invite
  - settings roundtrip; invite returns links and stores client email
3) Execute Uses Settings
  - dry-run task uses tenant DB IDs

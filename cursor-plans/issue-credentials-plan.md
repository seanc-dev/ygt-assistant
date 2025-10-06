# Issue Credentials & First-Login Password Change Plan

## Goals

- Admin can issue credentials for a client (email + temp password)
- Client can log in via client-ui
- On first login, client must change password (modal with generator + strength)

## Backend

- Tables: users(id, tenant_id, email, name, password_hash, must_change_password, created_at); client_sessions(token, user_id, created_at, expires_at)
- POST /admin/tenants/{tenant_id}/issue-credentials: upsert user with temp password, send email
- POST /api/auth/login: verify and set client cookie; return user info
- POST /api/auth/change-password: when must_change_password=true, allow without current password; otherwise require current
- GET /api/profile: return user profile + must_change_password

## Client-UI

- NextAuth CredentialsProvider authorize fetch uses credentials: include
- Remove self-register link and route access
- On dashboard mount, fetch /api/profile; if must_change_password, open modal
- Modal: new password input, generator button, strength meter; submit to /api/auth/change-password

## Admin-UI

- Setup page: add "Issue Login Credentials" button calling admin endpoint

## Tests

- Backend unit tests:
  - issue-credentials: creates user with must_change_password=true; sends mail (mock)
  - login success/failure; cookie set
  - change-password when must_change_password=true (no current required)
  - change-password when false (requires current)
  - profile returns must_change_password flag

## CI

- Tag tests with @feature(issue-credentials) and run subset on PR; full suite on main

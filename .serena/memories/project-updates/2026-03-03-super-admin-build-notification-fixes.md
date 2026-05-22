## Date
2026-03-03

## Summary of updates
Implemented and shipped 3 related fixes:

1) Super Admin access control moved to env-based identity
- Backend now resolves super admin by `SUPER_ADMIN_EMAIL` (environment variable), not hardcoded email checks.
- `require_super_admin` enforces email-based gate and returns clear 500 if `SUPER_ADMIN_EMAIL` is missing.
- `get_current_user` syncs `user.is_super_admin` to match configured email when env is present.
- Auth payloads (`/auth/login`, `/auth/verify-email`, `/auth/me`) now return effective `is_super_admin` from email check.
- Frontend Profile page super-admin link now uses `user.is_super_admin` instead of string email comparison.
- Added `SUPER_ADMIN_EMAIL=your-email@example.com` in `.env.example`.

2) Frontend production build blocker fixed
- `src/lib/services/superAdminApi.js` imported `authHeaders` from `api.js` but `api.js` did not export it.
- Fixed by exporting `authHeaders` from `src/lib/services/api.js`.
- `npm run build` now succeeds.

3) Notification panel clipping/layout fix in sidebar
- Notification dropdown was getting cut due to placement behavior in transformed sidebar context.
- Updated `NotificationBell.svelte`:
  - switched panel from fixed viewport placement to anchored absolute placement beside bell (`left-full` with margin),
  - removed old fullscreen backdrop approach,
  - added click-outside close behavior,
  - added Escape key close behavior,
  - minor panel header visual polish.
- Verified build still passes.

## Git commits pushed
- `c148170` - Fix super admin access via env-configured email
- `f91091a` - Fix frontend build by exporting authHeaders
- `852390d` - Fix notification panel clipping and interaction behavior

## Operational note
For super admin access to work in runtime, `.env` must include:
`SUPER_ADMIN_EMAIL=<owner_email>`
and backend should be restarted after env update.

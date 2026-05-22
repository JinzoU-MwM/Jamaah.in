## Date
2026-03-03

## Major updates completed

### 1) User-side Support Chat Bubble (frontend)
- Added floating support chat widget at bottom-right for authenticated users.
- Users can:
  - create new ticket,
  - browse existing tickets,
  - open ticket detail,
  - send replies in chat-style UI,
  - get periodic refresh while panel open.
- Files:
  - `frontend-svelte/src/lib/components/SupportChatBubble.svelte` (new)
  - `frontend-svelte/src/App.svelte` (integration; hidden on landing/login/public/super-admin pages)

### 2) Super Admin real-time ticket notifications
- Backend unread logic fixed and enhanced:
  - corrected unread detection to track unread USER messages,
  - added per-ticket `unread_user_messages`,
  - sorting ticket list by `updated_at` desc.
- Added endpoint:
  - `GET /super-admin/tickets/unread-count`
  - returns `{ unread_tickets, unread_messages }`.
- Frontend super-admin dashboard now:
  - polls unread count every 15s,
  - shows unread badge on Tickets tab,
  - marks rows with `NEW <count>` in ticket list,
  - triggers browser notification when unread messages increase (if permission granted).
- Files:
  - `backend/app/routers/super_admin_router.py`
  - `frontend-svelte/src/lib/services/superAdminApi.js`
  - `frontend-svelte/src/lib/pages/SuperAdminDashboard.svelte`
  - `frontend-svelte/src/lib/components/super-admin/TicketList.svelte`

### 3) Email notifications for support tickets
- Added admin email notifications for:
  - new user ticket,
  - user reply in existing ticket.
- Triggered asynchronously with FastAPI `BackgroundTasks` in user ticket router.
- Recipient resolution:
  - `SUPPORT_NOTIFY_EMAIL` (primary)
  - fallback `SUPER_ADMIN_EMAIL`.
- Files:
  - `backend/app/services/email_service.py`
  - `backend/app/routers/ticket_router.py`
  - `.env.example` (`SUPPORT_NOTIFY_EMAIL`)

### 4) Security hardening done in same workstream
- Removed traceback leak from global 500 responses.
- Safer CORS behavior:
  - explicit origins list parsing,
  - production fails if wildcard `*` used,
  - `allow_credentials=False` in current config.
- Added security headers:
  - CSP,
  - COOP,
  - CORP,
  - existing security headers retained.
- Locked `/auth/test-email`:
  - super-admin only,
  - disabled unless `ENABLE_TEST_EMAIL_ENDPOINT=true`,
  - recipient from env (`TEST_EMAIL_RECIPIENT`, fallback admin email).
- Removed DB write side-effects from `get_current_user`.
- Auth email sends refactored to FastAPI `BackgroundTasks` for register/resend/forgot flows.
- Files:
  - `backend/main.py`
  - `backend/app/auth.py`
  - `backend/app/routers/auth_router.py`

### 5) Email provider logic status
- Brevo logic remains available in `email_service.py` with SMTP fallback (restored per user request).

## Git
- Commit pushed: `d179d74`
- Message: `Add user support chat and admin ticket notifications`

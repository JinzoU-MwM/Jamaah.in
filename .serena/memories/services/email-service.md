# Email Service — Resend Integration

## Provider
- **Primary**: Resend SMTP relay (`smtp.resend.com:465`, SSL)
- **Fallback 1**: Resend HTTP API (`api.resend.com`) — blocked on some VPS IPs by Cloudflare WAF (error code 1010)
- **Fallback 2**: Generic SMTP (`SMTP_HOST`, `SMTP_PORT`)

## Why SMTP relay over HTTP API
The VPS IP/ASN is blocked by Cloudflare WAF protecting `api.resend.com`. The SMTP relay (`smtp.resend.com:465`) uses TLS/SMTP protocol which bypasses this block.

## Env Vars (in `.env.production` on server, loaded via `python-dotenv`)
```
RESEND_API_KEY=re_...       # Resend API key (also used as SMTP password for relay)
SMTP_EMAIL=no-reply@jamaah.web.id  # From address — must be verified domain in Resend
```
> Note: `.env.production` had a duplicate `SMTP_EMAIL` entry — dotenv resolves to last value (`no-reply@jamaah.web.id`).

## Key Files
- `backend/app/services/email_service.py` — `_send_via_resend_smtp`, `_send_via_resend_api`, `_send_via_smtp`, `_send_email`
- `backend/app/routers/auth_router.py` — `/auth/register`, `/auth/resend-otp`, `/auth/forgot-password`, `/auth/test-email`
- `backend/tests/test_email_service.py` — 19 unit tests (no real HTTP calls, mocked)

## SMTP Relay Credentials
- Host: `smtp.resend.com`, Port: `465` (SSL)
- Username: `resend`
- Password: `RESEND_API_KEY` value

## Email Functions
- `send_otp_email(to, otp_code)` — registration verification, 10-min expiry
- `send_reset_email(to, reset_code)` — password reset, 15-min expiry
- `send_support_new_ticket_email(...)` — notify super admin of new ticket
- `send_support_user_reply_email(...)` — notify super admin of user reply

## Deployment Note
Container is built from Dockerfile (no live source mount). To hot-patch:
```bash
docker cp file.py jamaah-backend:/app/backend/path/to/file.py
```

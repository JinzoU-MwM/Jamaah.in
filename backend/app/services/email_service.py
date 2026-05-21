"""
Email service — sends OTP and password-reset emails via Resend SMTP relay.
Falls back to generic SMTP if RESEND_API_KEY is not set.

Resend SMTP relay (smtp.resend.com:465) is used instead of the HTTP API because
some VPS IPs are blocked by Cloudflare WAF on api.resend.com.
"""
import os
import random
import json
import logging
import urllib.request
import urllib.error
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

SMTP_EMAIL = os.getenv("SMTP_EMAIL", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.hostinger.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_LOGIN = os.getenv("SMTP_LOGIN", "")
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
APP_NAME = "Jamaah.in"

# Resend SMTP relay constants
_RESEND_SMTP_HOST = "smtp.resend.com"
_RESEND_SMTP_PORT = 465  # SSL


def generate_otp() -> str:
    """Generate a 6-digit OTP code."""
    return str(random.randint(100000, 999999))


def _send_via_resend_smtp(to: str, subject: str, html_body: str) -> bool:
    """Send via Resend SMTP relay (avoids HTTP API Cloudflare blocks)."""
    if not RESEND_API_KEY:
        return False

    from_email = SMTP_EMAIL or "noreply@jamaah.in"
    msg = MIMEMultipart("alternative")
    msg["From"] = f"{APP_NAME} <{from_email}>"
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html"))

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(_RESEND_SMTP_HOST, _RESEND_SMTP_PORT, context=context) as server:
            server.login("resend", RESEND_API_KEY)
            server.sendmail(from_email, to, msg.as_string())
        logger.info("Resend SMTP email sent to %s: %s", to, subject)
        return True
    except Exception as e:
        logger.error("Resend SMTP failed for %s: %s", to, str(e))
        return False


def _send_via_resend_api(to: str, subject: str, html_body: str) -> bool:
    """Send email via Resend HTTP API (kept as secondary attempt after SMTP)."""
    if not RESEND_API_KEY:
        return False

    from_email = SMTP_EMAIL or "noreply@jamaah.in"
    payload = json.dumps({
        "from": f"{APP_NAME} <{from_email}>",
        "to": [to],
        "subject": subject,
        "html": html_body,
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=payload,
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        resp = urllib.request.urlopen(req)
        result = json.loads(resp.read())
        logger.info("Resend API email sent to %s: %s (id: %s)", to, subject, result.get("id"))
        return True
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        logger.error("Resend API error %d for %s: %s", e.code, to, body)
        return False
    except Exception as e:
        logger.error("Resend API failed for %s: %s", to, str(e))
        return False


def _send_via_smtp(to: str, subject: str, html_body: str) -> bool:
    """Send email via generic SMTP (final fallback)."""
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        logger.warning("SMTP not configured — skipping email to %s", to)
        return False

    msg = MIMEMultipart("alternative")
    msg["From"] = f"{APP_NAME} <{SMTP_EMAIL}>"
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(SMTP_LOGIN or SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(SMTP_EMAIL, to, msg.as_string())
        logger.info("SMTP email sent to %s: %s", to, subject)
        return True
    except Exception as e:
        logger.error("SMTP failed for %s: %s", to, str(e))
        return False


def _send_email(to: str, subject: str, html_body: str) -> bool:
    """Send email — Resend SMTP relay → Resend API → generic SMTP."""
    if RESEND_API_KEY:
        if _send_via_resend_smtp(to, subject, html_body):
            return True
        return _send_via_resend_api(to, subject, html_body)
    return _send_via_smtp(to, subject, html_body)


def send_otp_email(to: str, otp_code: str) -> bool:
    """Send registration OTP verification email."""
    subject = f"Kode Verifikasi {APP_NAME} — {otp_code}"
    html = f"""
    <div style="font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 520px; margin: 0 auto; padding: 32px 16px; background: #f8fafc;">
      <div style="background: #ffffff; border-radius: 16px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.07), 0 2px 4px -2px rgba(0,0,0,0.05); overflow: hidden;">

        <div style="height: 4px; background: linear-gradient(90deg, #2563eb, #1d4ed8);"></div>

        <div style="padding: 36px 32px;">

          <div style="text-align: center; margin-bottom: 28px;">
            <span style="font-size: 22px; font-weight: 900; letter-spacing: -0.5px; color: #0f172a;">Jamaah<span style="color: #10b981;">.in</span></span>
          </div>

          <div style="text-align: center; margin-bottom: 20px;">
            <span style="display: inline-block; background: #eff6ff; border-radius: 8px; padding: 5px 14px; font-size: 11px; font-weight: 700; color: #2563eb; letter-spacing: 0.08em; text-transform: uppercase;">Verifikasi Email</span>
          </div>

          <h1 style="margin: 0 0 12px; font-size: 20px; font-weight: 700; color: #0f172a; text-align: center; line-height: 1.3;">Kode Verifikasi Anda</h1>

          <p style="color: #475569; font-size: 15px; line-height: 1.6; margin: 0 0 28px; text-align: center;">
            Masukkan kode berikut untuk memverifikasi alamat email Anda.
          </p>

          <div style="text-align: center; margin: 0 0 28px;">
            <div style="display: inline-block; background: linear-gradient(135deg, #2563eb, #1d4ed8); border-radius: 14px; padding: 20px 40px; box-shadow: 0 4px 14px rgba(37,99,235,0.30);">
              <div style="letter-spacing: 12px; font-size: 36px; font-weight: 800; color: #ffffff; text-indent: 12px;">{otp_code}</div>
            </div>
          </div>

          <p style="color: #94a3b8; font-size: 13px; text-align: center; margin: 0;">
            Kode berlaku selama <strong style="color: #64748b;">10 menit</strong>. Jangan bagikan kode ini kepada siapapun.
          </p>

        </div>

        <div style="height: 1px; background: #f1f5f9; margin: 0 32px;"></div>

        <div style="padding: 18px 32px; text-align: center;">
          <p style="margin: 0; font-size: 12px; color: #94a3b8;">Jika Anda tidak membuat akun, abaikan email ini.</p>
        </div>
      </div>

      <p style="text-align: center; color: #cbd5e1; font-size: 12px; margin-top: 20px;">© 2026 Jamaah.in · All rights reserved</p>
    </div>
    """
    return _send_email(to, subject, html)


def send_reset_email(to: str, reset_code: str) -> bool:
    """Send password reset code email."""
    subject = f"Reset Password {APP_NAME} — {reset_code}"
    html = f"""
    <div style="font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 520px; margin: 0 auto; padding: 32px 16px; background: #f8fafc;">
      <div style="background: #ffffff; border-radius: 16px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.07), 0 2px 4px -2px rgba(0,0,0,0.05); overflow: hidden;">

        <div style="height: 4px; background: linear-gradient(90deg, #f59e0b, #d97706);"></div>

        <div style="padding: 36px 32px;">

          <div style="text-align: center; margin-bottom: 28px;">
            <span style="font-size: 22px; font-weight: 900; letter-spacing: -0.5px; color: #0f172a;">Jamaah<span style="color: #10b981;">.in</span></span>
          </div>

          <div style="text-align: center; margin-bottom: 20px;">
            <span style="display: inline-block; background: #fffbeb; border-radius: 8px; padding: 5px 14px; font-size: 11px; font-weight: 700; color: #d97706; letter-spacing: 0.08em; text-transform: uppercase;">Reset Password</span>
          </div>

          <h1 style="margin: 0 0 12px; font-size: 20px; font-weight: 700; color: #0f172a; text-align: center; line-height: 1.3;">Kode Reset Password</h1>

          <p style="color: #475569; font-size: 15px; line-height: 1.6; margin: 0 0 28px; text-align: center;">
            Kami menerima permintaan reset password. Gunakan kode berikut untuk melanjutkan.
          </p>

          <div style="text-align: center; margin: 0 0 28px;">
            <div style="display: inline-block; background: linear-gradient(135deg, #f59e0b, #d97706); border-radius: 14px; padding: 20px 40px; box-shadow: 0 4px 14px rgba(245,158,11,0.30);">
              <div style="letter-spacing: 12px; font-size: 36px; font-weight: 800; color: #ffffff; text-indent: 12px;">{reset_code}</div>
            </div>
          </div>

          <p style="color: #94a3b8; font-size: 13px; text-align: center; margin: 0;">
            Kode berlaku selama <strong style="color: #64748b;">15 menit</strong>. Abaikan email ini jika Anda tidak meminta reset password.
          </p>

        </div>

        <div style="height: 1px; background: #f1f5f9; margin: 0 32px;"></div>

        <div style="padding: 18px 32px; text-align: center;">
          <p style="margin: 0; font-size: 12px; color: #94a3b8;">Jika Anda tidak meminta ini, akun Anda tetap aman. Tidak ada tindakan yang diperlukan.</p>
        </div>
      </div>

      <p style="text-align: center; color: #cbd5e1; font-size: 12px; margin-top: 20px;">© 2026 Jamaah.in · All rights reserved</p>
    </div>
    """
    return _send_email(to, subject, html)


def _support_notify_recipient() -> str:
    """Recipient for support notifications (super admin inbox)."""
    return (
        os.getenv("SUPPORT_NOTIFY_EMAIL", "").strip()
        or os.getenv("SUPER_ADMIN_EMAIL", "").strip()
    )


def send_support_new_ticket_email(
    user_name: str,
    user_email: str,
    ticket_id: int,
    subject_text: str,
    message_preview: str,
) -> bool:
    """Notify super admin that a user created a new support ticket."""
    to = _support_notify_recipient()
    if not to:
        logger.warning("Support notify recipient not configured; skipping new-ticket email.")
        return False

    subject = f"[Support] Tiket Baru #{ticket_id} - {subject_text}"
    html = f"""
    <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 560px; margin: 0 auto; padding: 24px; background: #f8fafc;">
      <div style="background: white; border-radius: 14px; padding: 24px; border: 1px solid #e2e8f0;">
        <h2 style="margin: 0 0 12px; color: #0f172a;">Tiket Support Baru</h2>
        <p style="margin: 0 0 6px; color: #334155;"><strong>Ticket ID:</strong> #{ticket_id}</p>
        <p style="margin: 0 0 6px; color: #334155;"><strong>User:</strong> {user_name} ({user_email})</p>
        <p style="margin: 0 0 6px; color: #334155;"><strong>Subjek:</strong> {subject_text}</p>
        <p style="margin: 12px 0 4px; color: #334155;"><strong>Pesan awal:</strong></p>
        <div style="padding: 12px; background: #f1f5f9; border-radius: 10px; color: #334155;">
          {message_preview}
        </div>
        <p style="margin-top: 16px; font-size: 13px; color: #64748b;">
          Buka Super Admin Dashboard untuk membalas tiket ini.
        </p>
      </div>
    </div>
    """
    return _send_email(to, subject, html)


def send_support_user_reply_email(
    user_name: str,
    user_email: str,
    ticket_id: int,
    subject_text: str,
    message_preview: str,
) -> bool:
    """Notify super admin that a user replied on an existing support ticket."""
    to = _support_notify_recipient()
    if not to:
        logger.warning("Support notify recipient not configured; skipping reply-notification email.")
        return False

    subject = f"[Support] Balasan User pada Ticket #{ticket_id}"
    html = f"""
    <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 560px; margin: 0 auto; padding: 24px; background: #f8fafc;">
      <div style="background: white; border-radius: 14px; padding: 24px; border: 1px solid #e2e8f0;">
        <h2 style="margin: 0 0 12px; color: #0f172a;">Balasan User Baru</h2>
        <p style="margin: 0 0 6px; color: #334155;"><strong>Ticket ID:</strong> #{ticket_id}</p>
        <p style="margin: 0 0 6px; color: #334155;"><strong>User:</strong> {user_name} ({user_email})</p>
        <p style="margin: 0 0 6px; color: #334155;"><strong>Subjek:</strong> {subject_text}</p>
        <p style="margin: 12px 0 4px; color: #334155;"><strong>Pesan terbaru:</strong></p>
        <div style="padding: 12px; background: #f1f5f9; border-radius: 10px; color: #334155;">
          {message_preview}
        </div>
        <p style="margin-top: 16px; font-size: 13px; color: #64748b;">
          Buka Super Admin Dashboard untuk membalas tiket ini.
        </p>
      </div>
    </div>
    """
    return _send_email(to, subject, html)

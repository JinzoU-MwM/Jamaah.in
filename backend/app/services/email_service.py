"""
Email service — sends OTP and password-reset emails via Brevo HTTP API.
Falls back to SMTP if BREVO_API_KEY is not set.
"""
import os
import random
import json
import logging
import urllib.request
import urllib.error
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

SMTP_EMAIL = os.getenv("SMTP_EMAIL", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp-relay.brevo.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_LOGIN = os.getenv("SMTP_LOGIN", "")
BREVO_API_KEY = os.getenv("BREVO_API_KEY", "") or os.getenv("BREVI_API_KEY", "")
APP_NAME = "Jamaah.in"


def generate_otp() -> str:
    """Generate a 6-digit OTP code."""
    return str(random.randint(100000, 999999))


def _send_via_brevo_api(to: str, subject: str, html_body: str) -> bool:
    """Send email via Brevo HTTP API (preferred)."""
    if not BREVO_API_KEY:
        return False

    payload = json.dumps({
        "sender": {"name": APP_NAME, "email": SMTP_EMAIL},
        "to": [{"email": to}],
        "subject": subject,
        "htmlContent": html_body,
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.brevo.com/v3/smtp/email",
        data=payload,
        headers={
            "api-key": BREVO_API_KEY,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    try:
        resp = urllib.request.urlopen(req)
        result = json.loads(resp.read())
        logger.info("Brevo API email sent to %s: %s (messageId: %s)", to, subject, result.get("messageId"))
        return True
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        logger.error("Brevo API error %d for %s: %s", e.code, to, body)
        return False
    except Exception as e:
        logger.error("Brevo API failed for %s: %s", to, str(e))
        return False


def _send_via_smtp(to: str, subject: str, html_body: str) -> bool:
    """Send email via SMTP (fallback)."""
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
    """Send email — tries Brevo API first, falls back to SMTP."""
    if BREVO_API_KEY:
        return _send_via_brevo_api(to, subject, html_body)
    return _send_via_smtp(to, subject, html_body)


def send_otp_email(to: str, otp_code: str) -> bool:
    """Send registration OTP verification email."""
    subject = f"Kode Verifikasi {APP_NAME} — {otp_code}"
    html = f"""
    <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 480px; margin: 0 auto; padding: 32px 24px; background: #f8fafc;">
        <div style="background: white; border-radius: 16px; padding: 32px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); border: 1px solid #e2e8f0;">
            <div style="text-align: center; margin-bottom: 24px;">
                <h1 style="color: #10b981; font-size: 24px; margin: 0;">🕌 {APP_NAME}</h1>
                <p style="color: #64748b; font-size: 14px; margin-top: 4px;">Verifikasi Email Anda</p>
            </div>
            <p style="color: #334155; font-size: 15px; line-height: 1.6;">
                Gunakan kode di bawah ini untuk memverifikasi alamat email Anda:
            </p>
            <div style="text-align: center; margin: 24px 0;">
                <div style="display: inline-block; background: linear-gradient(135deg, #d1fae5, #cffafe); padding: 16px 32px; border-radius: 12px; letter-spacing: 8px; font-size: 32px; font-weight: 700; color: #059669;">
                    {otp_code}
                </div>
            </div>
            <p style="color: #94a3b8; font-size: 13px; text-align: center;">
                Kode berlaku selama <strong>10 menit</strong>. Jangan bagikan kode ini kepada siapapun.
            </p>
        </div>
        <p style="text-align: center; color: #94a3b8; font-size: 12px; margin-top: 16px;">© 2026 {APP_NAME}</p>
    </div>
    """
    return _send_email(to, subject, html)


def send_reset_email(to: str, reset_code: str) -> bool:
    """Send password reset code email."""
    subject = f"Reset Password {APP_NAME} — {reset_code}"
    html = f"""
    <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 480px; margin: 0 auto; padding: 32px 24px; background: #f8fafc;">
        <div style="background: white; border-radius: 16px; padding: 32px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); border: 1px solid #e2e8f0;">
            <div style="text-align: center; margin-bottom: 24px;">
                <h1 style="color: #10b981; font-size: 24px; margin: 0;">🕌 {APP_NAME}</h1>
                <p style="color: #64748b; font-size: 14px; margin-top: 4px;">Reset Password</p>
            </div>
            <p style="color: #334155; font-size: 15px; line-height: 1.6;">
                Kami menerima permintaan reset password. Gunakan kode berikut:
            </p>
            <div style="text-align: center; margin: 24px 0;">
                <div style="display: inline-block; background: linear-gradient(135deg, #fef3c7, #fde68a); padding: 16px 32px; border-radius: 12px; letter-spacing: 8px; font-size: 32px; font-weight: 700; color: #b45309;">
                    {reset_code}
                </div>
            </div>
            <p style="color: #94a3b8; font-size: 13px; text-align: center;">
                Kode berlaku selama <strong>15 menit</strong>. Abaikan email ini jika Anda tidak meminta reset password.
            </p>
        </div>
        <p style="text-align: center; color: #94a3b8; font-size: 12px; margin-top: 16px;">© 2026 {APP_NAME}</p>
    </div>
    """
    return _send_email(to, subject, html)

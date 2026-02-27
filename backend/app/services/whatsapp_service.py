"""
WhatsApp OTP Service — Fonnte API Integration
Sends OTP codes via WhatsApp for phone verification.
"""
import os
import random
import string
import logging
import urllib.request
import urllib.error
import json
from datetime import datetime, timedelta
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Fonnte API configuration
FONNTE_TOKEN = os.getenv("FONNTE_TOKEN", "")
FONNTE_API_URL = "https://api.fonnte.com/send"

# OTP configuration
OTP_LENGTH = 6
OTP_EXPIRY_MINUTES = 5


def generate_otp() -> str:
    """Generate a random 6-digit OTP code."""
    return ''.join(random.choices(string.digits, k=OTP_LENGTH))


def format_phone_number(phone: str) -> str:
    """
    Format phone number to Indonesian format with country code.
    Examples:
    - 081234567890 -> 6281234567890
    - 6281234567890 -> 6281234567890
    - +6281234567890 -> 6281234567890
    """
    # Remove any non-digit characters
    phone = ''.join(filter(str.isdigit, phone))

    # Handle Indonesian numbers
    if phone.startswith('0'):
        phone = '62' + phone[1:]
    elif phone.startswith('+62'):
        phone = phone[3:]
    elif not phone.startswith('62'):
        phone = '62' + phone

    return phone


def send_whatsapp_otp(phone_number: str, otp_code: str) -> Tuple[bool, str]:
    """
    Send OTP via WhatsApp using Fonnte API.

    Returns:
        Tuple of (success: bool, message: str)
    """
    if not FONNTE_TOKEN:
        # Development mode - log OTP instead of sending
        logger.warning("FONNTE_TOKEN not set - OTP would be sent to %s: %s", phone_number, otp_code)
        return True, f"DEV MODE: OTP is {otp_code}"

    formatted_phone = format_phone_number(phone_number)

    message = f"""🔐 *Kode Verifikasi Jamaah.in*

Kode OTP Anda: *{otp_code}*

Kode ini berlaku selama {OTP_EXPIRY_MINUTES} menit.
Jangan bagikan kode ini kepada siapapun.

- Tim Jamaah.in"""

    payload = json.dumps({
        "target": formatted_phone,
        "message": message,
        "countryCode": "62",
    }).encode('utf-8')

    headers = {
        "Authorization": FONNTE_TOKEN,
        "Content-Type": "application/json",
    }

    try:
        req = urllib.request.Request(
            FONNTE_API_URL,
            data=payload,
            headers=headers,
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))

            if result.get('status', False):
                logger.info("WhatsApp OTP sent successfully to %s", formatted_phone)
                return True, "OTP berhasil dikirim ke WhatsApp Anda"
            else:
                error_msg = result.get('reason', 'Unknown error')
                logger.error("Failed to send WhatsApp OTP: %s", error_msg)
                return False, f"Gagal mengirim OTP: {error_msg}"

    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else ''
        logger.error("HTTP error sending WhatsApp OTP: %s - %s", e.code, error_body)
        return False, f"Gagal mengirim OTP (HTTP {e.code})"
    except urllib.error.URLError as e:
        logger.error("URL error sending WhatsApp OTP: %s", e.reason)
        return False, f"Gagal mengirim OTP: {e.reason}"
    except Exception as e:
        logger.exception("Unexpected error sending WhatsApp OTP")
        return False, f"Gagal mengirim OTP: {str(e)}"


def verify_otp(provided_otp: str, stored_otp: str, expires_at: datetime) -> Tuple[bool, str]:
    """
    Verify the provided OTP against stored OTP.

    Returns:
        Tuple of (valid: bool, message: str)
    """
    if not stored_otp:
        return False, "Kode OTP tidak ditemukan. Silakan minta kode baru."

    if datetime.utcnow() > expires_at:
        return False, "Kode OTP sudah kedaluwarsa. Silakan minta kode baru."

    if provided_otp != stored_otp:
        return False, "Kode OTP tidak valid. Silakan coba lagi."

    return True, "Kode OTP valid"


def create_otp_expiry() -> datetime:
    """Create expiry datetime for OTP (5 minutes from now)."""
    return datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES)

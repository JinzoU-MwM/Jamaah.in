"""
Payment service — Pakasir payment gateway integration.
Handles payment URL generation and transaction verification.
"""
import os
import json
import logging
import urllib.request
import urllib.error
from datetime import datetime

logger = logging.getLogger(__name__)

PAKASIR_SLUG = os.getenv("PAKASIR_SLUG", "") or os.getenv("SLUG", "")
PAKASIR_API_KEY = os.getenv("PAKASIR_API_KEY", "")
PAKASIR_BASE_URL = "https://app.pakasir.com"

# Pricing constants
PRO_PRICE_MONTHLY = 80000  # Rp 80.000 per month
PRO_PRICE_ANNUAL = 800000  # Rp 800.000 per year (save ~17% = 2 months free)
# Legacy alias for backward compatibility
PRO_PRICE = PRO_PRICE_MONTHLY
PRO_ANNUAL_PRICE = PRO_PRICE_ANNUAL


def create_payment_url(order_id: str, amount: int = PRO_PRICE, redirect_url: str = None) -> str:
    """
    Build Pakasir payment URL.
    Format: https://app.pakasir.com/pay/{slug}/{amount}?order_id={order_id}&redirect={redirect_url}
    """
    from urllib.parse import quote

    if not PAKASIR_SLUG:
        raise ValueError("PAKASIR_SLUG not configured")

    url = f"{PAKASIR_BASE_URL}/pay/{PAKASIR_SLUG}/{amount}?order_id={order_id}"
    if redirect_url:
        url += f"&redirect={quote(redirect_url, safe='')}"
    return url


def verify_transaction(order_id: str) -> dict:
    """
    Verify transaction status via Pakasir API.
    Returns dict with transaction details or None on error.
    """
    if not PAKASIR_API_KEY:
        logger.error("PAKASIR_API_KEY not configured")
        return None

    url = f"{PAKASIR_BASE_URL}/api/v1/transaction/{order_id}"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {PAKASIR_API_KEY}",
            "Accept": "application/json",
        },
    )

    try:
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read())
        logger.info("Pakasir verify order %s: %s", order_id, data.get("status"))
        return data
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        logger.error("Pakasir API error %d for order %s: %s", e.code, order_id, body)
        return None
    except Exception as e:
        logger.error("Pakasir API failed for order %s: %s", order_id, str(e))
        return None

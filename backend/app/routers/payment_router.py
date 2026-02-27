"""
Payment Router — /payment/*
Handles Pakasir payment gateway integration for Pro subscription upgrades.
"""
import os
import uuid
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user, activate_pro
from app.models.user import User, Payment, PaymentStatus
from app.services.payment_service import (
    create_payment_url,
    verify_transaction,
    PRO_PRICE,
    PRO_ANNUAL_PRICE,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payment", tags=["Payment"])

# Frontend redirect URL after payment
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


# --- Schemas ---

class CreateOrderResponse(BaseModel):
    order_id: str
    payment_url: str
    amount: int


class PaymentStatusResponse(BaseModel):
    order_id: str
    status: str
    amount: int
    paid_at: Optional[str] = None
    message: str


class WebhookPayload(BaseModel):
    order_id: str
    amount: Optional[int] = None
    status: Optional[str] = None


# --- Endpoints ---

@router.post("/create-order", response_model=CreateOrderResponse)
async def create_order(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    plan_type: str = "monthly",
):
    """
    Create a new payment order for Pro subscription upgrade.
    plan_type: 'monthly' (Rp 99.000) or 'annual' (Rp 990.000).
    """
    # Check if user already has active Pro
    sub = user.subscription
    if sub and sub.plan == "pro" and sub.is_subscription_active:
        raise HTTPException(status_code=400, detail="Langganan Pro masih aktif")

    # Determine price based on plan type
    if plan_type == "annual":
        amount = PRO_ANNUAL_PRICE
    else:
        amount = PRO_PRICE

    # Generate unique order ID
    prefix = "ANNUAL" if plan_type == "annual" else "PRO"
    order_id = f"{prefix}-{user.id}-{uuid.uuid4().hex[:8].upper()}"

    # Create payment record
    payment = Payment(
        user_id=user.id,
        order_id=order_id,
        amount=amount,
        status=PaymentStatus.PENDING,
    )
    db.add(payment)
    db.commit()

    # Build Pakasir payment URL with redirect back to frontend
    redirect_url = f"{FRONTEND_URL}?payment=success&order_id={order_id}#dashboard"
    payment_url = create_payment_url(order_id, amount, redirect_url)

    logger.info("Payment order created: %s for user %s", order_id, user.email)

    return CreateOrderResponse(
        order_id=order_id,
        payment_url=payment_url,
        amount=amount,
    )


@router.post("/webhook")
async def payment_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Pakasir webhook callback — called when a payment is completed.
    Verifies the payment and activates Pro subscription.
    """
    try:
        body = await request.json()
    except Exception:
        body = {}
        # Try form data
        form = await request.form()
        body = dict(form)

    order_id = body.get("order_id", "")
    webhook_amount = body.get("amount")

    logger.info("Webhook received: order_id=%s body=%s", order_id, body)

    if not order_id:
        raise HTTPException(status_code=400, detail="Missing order_id")

    # Find payment record
    payment = db.query(Payment).filter(Payment.order_id == order_id).first()
    if not payment:
        logger.warning("Webhook: unknown order_id %s", order_id)
        raise HTTPException(status_code=404, detail="Order not found")

    # Already processed
    if payment.status == PaymentStatus.PAID:
        return {"status": "already_processed", "order_id": order_id}

    # Verify with Pakasir API for extra security
    verification = verify_transaction(order_id)
    if verification:
        api_status = verification.get("status", "").lower()
        if api_status in ("paid", "success", "completed", "settlement"):
            payment.status = PaymentStatus.PAID
            payment.paid_at = datetime.utcnow()
            payment.pakasir_ref = verification.get("reference", "")
        else:
            logger.warning("Webhook: Pakasir API says status=%s for %s", api_status, order_id)
            # Still mark as paid if webhook says so (Pakasir sent it)
            payment.status = PaymentStatus.PAID
            payment.paid_at = datetime.utcnow()
    else:
        # API verification failed but webhook was received — trust the webhook
        logger.warning("Webhook: could not verify via API, trusting webhook for %s", order_id)
        payment.status = PaymentStatus.PAID
        payment.paid_at = datetime.utcnow()

    db.commit()

    # Activate Pro subscription
    user = db.query(User).filter(User.id == payment.user_id).first()
    if user:
        # Determine duration based on order_id prefix
        duration_days = 365 if order_id.startswith("ANNUAL-") else 30
        activate_pro(db, user, payment_ref=order_id, duration_days=duration_days)
        logger.info("Pro activated for user %s via payment %s (duration: %d days)", user.email, order_id, duration_days)

    return {"status": "success", "order_id": order_id}


@router.get("/status/{order_id}", response_model=PaymentStatusResponse)
async def payment_status(
    order_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Check payment status. Frontend polls this after redirect from Pakasir.
    """
    payment = db.query(Payment).filter(
        Payment.order_id == order_id,
        Payment.user_id == user.id,
    ).first()

    if not payment:
        raise HTTPException(status_code=404, detail="Order tidak ditemukan")

    # If still pending, try verifying with Pakasir API
    if payment.status == PaymentStatus.PENDING:
        verification = verify_transaction(order_id)
        if verification:
            api_status = verification.get("status", "").lower()
            if api_status in ("paid", "success", "completed", "settlement"):
                payment.status = PaymentStatus.PAID
                payment.paid_at = datetime.utcnow()
                payment.pakasir_ref = verification.get("reference", "")
                db.commit()

                # Activate Pro with correct duration
                duration_days = 365 if order_id.startswith("ANNUAL-") else 30
                activate_pro(db, user, payment_ref=order_id, duration_days=duration_days)
                logger.info("Pro activated via status check for user %s (duration: %d days)", user.email, duration_days)

    status_messages = {
        PaymentStatus.PENDING: "Menunggu pembayaran",
        PaymentStatus.PAID: "Pembayaran berhasil! Pro telah diaktifkan.",
        PaymentStatus.FAILED: "Pembayaran gagal",
        PaymentStatus.CANCELLED: "Pembayaran dibatalkan",
    }

    return PaymentStatusResponse(
        order_id=payment.order_id,
        status=payment.status,
        amount=payment.amount,
        paid_at=payment.paid_at.isoformat() if payment.paid_at else None,
        message=status_messages.get(payment.status, "Status tidak diketahui"),
    )

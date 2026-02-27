"""
Subscription Router — /subscription/*
Handles subscription status, upgrade requests, and payment tracking.
"""
from datetime import datetime, timedelta
from typing import Optional, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user, check_access, activate_pro, verify_password
from app.models.user import User

router = APIRouter(prefix="/subscription", tags=["Subscription"])


# --- Schemas ---

class SubscriptionStatusResponse(BaseModel):
    allowed: bool
    plan: str
    status: str
    usage_count: int
    usage_limit: Optional[int]
    trial_ends: Optional[str]
    subscription_ends: Optional[str]
    message: str


class UpgradeRequest(BaseModel):
    payment_ref: Optional[str] = None  # manual payment receipt reference
    plan_type: Optional[Literal["monthly", "annual"]] = "monthly"  # monthly or annual


class UpgradeResponse(BaseModel):
    success: bool
    plan: str
    status: str
    expires_at: str
    message: str


class PricingInfo(BaseModel):
    free_scans: int
    pro_trial_days: int
    monthly: int
    annual: int
    monthly_display: str
    annual_display: str
    annual_savings: str


class ActivateTrialRequest(BaseModel):
    pass  # No additional data needed - uses verified phone


class TrialStatusResponse(BaseModel):
    can_activate: bool
    phone_verified: bool
    trial_used: bool
    message: str


# --- Endpoints ---

@router.get("/status", response_model=SubscriptionStatusResponse)
async def subscription_status(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current subscription status + usage info."""
    return check_access(db, user)


@router.get("/pricing", response_model=PricingInfo)
async def get_pricing():
    """Get current pricing information."""
    return PricingInfo(
        free_scans=5,
        pro_trial_days=7,
        monthly=80000,
        annual=800000,
        monthly_display="Rp 80.000/bulan",
        annual_display="Rp 800.000/tahun",
        annual_savings="Hemat 17% (2 bulan gratis)"
    )


@router.get("/trial-status", response_model=TrialStatusResponse)
async def trial_status(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Check if user can activate Pro Trial."""
    # Check if phone is verified
    phone_verified = user.phone_verified or False

    # Check if trial already used
    trial_used = user.trial_used_at is not None

    # Can activate if phone is verified and trial not used
    can_activate = phone_verified and not trial_used

    if trial_used:
        message = "Anda sudah pernah menggunakan Pro Trial"
    elif not phone_verified:
        message = "Verifikasi nomor WhatsApp terlebih dahulu"
    else:
        message = "Anda bisa mengaktifkan Pro Trial 7 hari"

    return TrialStatusResponse(
        can_activate=can_activate,
        phone_verified=phone_verified,
        trial_used=trial_used,
        message=message
    )


@router.post("/activate-trial", response_model=UpgradeResponse)
async def activate_trial(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Activate 7-day Pro Trial.
    Requirements:
    - Phone must be verified
    - Trial not previously used
    """
    # Check phone verification
    if not user.phone_verified:
        raise HTTPException(
            status_code=400,
            detail="Verifikasi nomor WhatsApp terlebih dahulu"
        )

    # Check if trial already used
    if user.trial_used_at:
        raise HTTPException(
            status_code=400,
            detail="Anda sudah pernah menggunakan Pro Trial. Upgrade ke Pro untuk melanjutkan."
        )

    # Activate 7-day Pro Trial
    sub = activate_pro(db, user, payment_ref="TRIAL", duration_days=7)

    # Mark trial as used
    user.trial_used_at = datetime.utcnow()
    db.commit()

    return UpgradeResponse(
        success=True,
        plan="pro_trial",
        status="active",
        expires_at=sub.expires_at.isoformat(),
        message="Pro Trial 7 hari berhasil diaktifkan! Nikmati semua fitur Pro.",
    )


@router.post("/upgrade", response_model=UpgradeResponse)
async def upgrade_to_pro(
    req: UpgradeRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upgrade to Pro plan.
    - Monthly: Rp 99.000 (30 days)
    - Annual: Rp 990.000 (365 days, save 17%)
    Accepts manual payment reference.
    """
    # Determine duration based on plan type
    if req.plan_type == "annual":
        duration_days = 365
        plan_name = "pro_annual"
        message = "Berhasil upgrade ke Pro Annual! Akses unlimited selama 1 tahun."
    else:
        duration_days = 30
        plan_name = "pro"
        message = "Berhasil upgrade ke Pro! Akses unlimited selama 30 hari."

    sub = activate_pro(db, user, payment_ref=req.payment_ref, duration_days=duration_days)
    return UpgradeResponse(
        success=True,
        plan=plan_name,
        status="active",
        expires_at=sub.expires_at.isoformat(),
        message=message,
    )

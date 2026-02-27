"""
Authentication & Authorization Module
- JWT token management
- Password hashing
- User registration & login
- Subscription/usage gating
"""
import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from bcrypt import hashpw, gensalt, checkpw
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.database import get_db
from app.models.user import User, Subscription, UsageLog, PlanType, SubscriptionStatus

# --- Config ---
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY environment variable is required. Set it in .env file.")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24
TRIAL_DAYS = 7
FREE_USAGE_LIMIT = 5  # Free tier: 5 scans lifetime

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# =============================================================================
# PASSWORD HASHING
# =============================================================================

def hash_password(password: str) -> str:
    return hashpw(password.encode("utf-8"), gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


# =============================================================================
# JWT TOKEN
# =============================================================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token tidak valid atau sudah kedaluwarsa",
            headers={"WWW-Authenticate": "Bearer"},
        )


# =============================================================================
# USER OPERATIONS
# =============================================================================

def register_user(db: Session, email: str, password: str, name: str) -> User:
    """Register a new user with a 7-day free trial. Sends OTP for verification."""
    from app.services.email_service import generate_otp, send_otp_email
    import threading

    # Check duplicate
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email sudah terdaftar")

    # Generate OTP
    otp = generate_otp()
    now = datetime.utcnow()

    # Create user (unverified)
    user = User(
        email=email.lower().strip(),
        name=name.strip(),
        password_hash=hash_password(password),
        email_verified=False,
        otp_code=hash_password(otp),
        otp_expires=now + timedelta(minutes=10),
    )
    db.add(user)
    db.flush()  # get user.id

    # Create subscription with 7-day trial
    subscription = Subscription(
        user_id=user.id,
        plan=PlanType.FREE,
        status=SubscriptionStatus.TRIAL,
        trial_start=now,
        trial_end=now + timedelta(days=TRIAL_DAYS),
    )
    db.add(subscription)
    db.commit()
    db.refresh(user)

    # Send OTP email in background thread so registration doesn't block
    def _send():
        try:
            send_otp_email(user.email, otp)
        except Exception as e:
            logging.getLogger(__name__).error("Failed to send OTP email to %s: %s", user.email, e)

    threading.Thread(target=_send, daemon=True).start()

    return user


def authenticate_user(db: Session, email: str, password: str) -> User:
    """Authenticate user by email and password."""
    user = db.query(User).filter(User.email == email.lower().strip()).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email atau password salah",
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Akun dinonaktifkan")
    if not user.email_verified:
        raise HTTPException(
            status_code=403,
            detail="Email belum diverifikasi. Silakan cek inbox Anda.",
            headers={"X-Unverified": "true"},
        )
    return user


# =============================================================================
# DEPENDENCIES (FastAPI)
# =============================================================================

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """FastAPI dependency: extract current user from JWT."""
    payload = decode_token(token)
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Token tidak valid")

    user = db.query(User).options(joinedload(User.subscription)).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=401, detail="User tidak ditemukan")
    return user


async def require_admin(
    user: User = Depends(get_current_user),
) -> User:
    """FastAPI dependency: require current user to be an admin."""
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akses admin diperlukan",
        )
    return user


# =============================================================================
# SUBSCRIPTION & USAGE CHECKS
# =============================================================================

def get_usage_count(db: Session, user_id: int) -> int:
    """Get total document scans for a user."""
    result = db.query(func.sum(UsageLog.count)).filter(UsageLog.user_id == user_id).scalar()
    return result or 0


def record_usage(db: Session, user_id: int, count: int = 1):
    """Record a document scan usage."""
    log = UsageLog(user_id=user_id, action="document_scan", count=count)
    db.add(log)
    db.commit()


def check_access(db: Session, user: User) -> dict:
    """
    Check if user can access the service.
    Returns: {
        "allowed": bool,
        "plan": "free" | "pro",
        "status": "trial" | "active" | "expired",
        "usage_count": int,
        "usage_limit": int | None,
        "trial_ends": str | None,
        "subscription_ends": str | None,
        "message": str
    }
    """
    sub = user.subscription
    usage = get_usage_count(db, user.id)

    if not sub:
        return {
            "allowed": False,
            "plan": "free",
            "status": "expired",
            "usage_count": usage,
            "usage_limit": FREE_USAGE_LIMIT,
            "trial_ends": None,
            "subscription_ends": None,
            "message": "Tidak ada langganan aktif",
        }

    # Pro subscriber
    if sub.plan == PlanType.PRO and sub.is_subscription_active:
        return {
            "allowed": True,
            "plan": "pro",
            "status": "active",
            "usage_count": usage,
            "usage_limit": None,  # unlimited
            "trial_ends": None,
            "subscription_ends": sub.expires_at.isoformat() if sub.expires_at else None,
            "message": "Langganan Pro aktif",
        }

    # Trial period
    if sub.is_trial_active:
        remaining = FREE_USAGE_LIMIT - usage
        return {
            "allowed": remaining > 0,
            "plan": "free",
            "status": "trial",
            "usage_count": usage,
            "usage_limit": FREE_USAGE_LIMIT,
            "trial_ends": sub.trial_end.isoformat() if sub.trial_end else None,
            "subscription_ends": None,
            "message": f"Trial aktif, sisa {max(0, remaining)} penggunaan" if remaining > 0
                       else "Batas penggunaan gratis tercapai. Upgrade ke Pro!",
        }

    # Trial expired, check if still under free usage limit
    remaining = FREE_USAGE_LIMIT - usage
    if remaining > 0:
        # Update status to expired
        if sub.status == SubscriptionStatus.TRIAL:
            sub.status = SubscriptionStatus.EXPIRED
            db.commit()
        return {
            "allowed": True,
            "plan": "free",
            "status": "expired",
            "usage_count": usage,
            "usage_limit": FREE_USAGE_LIMIT,
            "trial_ends": sub.trial_end.isoformat() if sub.trial_end else None,
            "subscription_ends": None,
            "message": f"Trial berakhir, sisa {remaining} penggunaan gratis",
        }

    # No access
    if sub.status != SubscriptionStatus.EXPIRED:
        sub.status = SubscriptionStatus.EXPIRED
        db.commit()
    return {
        "allowed": False,
        "plan": "free",
        "status": "expired",
        "usage_count": usage,
        "usage_limit": FREE_USAGE_LIMIT,
        "trial_ends": sub.trial_end.isoformat() if sub.trial_end else None,
        "subscription_ends": None,
        "message": "Batas penggunaan gratis tercapai. Upgrade ke Pro!",
    }


def activate_pro(db: Session, user: User, payment_ref: str = None, duration_days: int = 30) -> Subscription:
    """Activate Pro subscription for specified duration (default 30 days)."""
    sub = user.subscription
    if not sub:
        sub = Subscription(user_id=user.id)
        db.add(sub)

    now = datetime.utcnow()
    sub.plan = PlanType.PRO
    sub.status = SubscriptionStatus.ACTIVE
    sub.subscribed_at = now
    sub.expires_at = now + timedelta(days=duration_days)
    sub.payment_ref = payment_ref
    db.commit()
    db.refresh(sub)
    return sub

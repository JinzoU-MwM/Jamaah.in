"""
Authentication Router — /auth/*
Handles user registration, login, email verification, password reset, and profile retrieval.
"""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import (
    register_user,
    authenticate_user,
    create_access_token,
    get_current_user,
    check_access,
    get_usage_count,
    verify_password,
    hash_password,
    FREE_USAGE_LIMIT,
)
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Rate limiter (uses the app-level limiter from main.py)
from slowapi import Limiter
from slowapi.util import get_remote_address
limiter = Limiter(key_func=get_remote_address)


# --- Request/Response Schemas ---

class RegisterRequest(BaseModel):
    email: str = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=100)


class LoginRequest(BaseModel):
    email: str = Field(max_length=255)
    password: str = Field(max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    is_admin: bool = False
    created_at: str
    avatar_color: str = "emerald"
    notify_usage_limit: bool = True
    notify_expiry: bool = True
    subscription: dict
    usage: dict


# --- Endpoints ---

@router.post("/register")
@limiter.limit("3/minute")
async def register(request: Request, req: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user. Sends OTP for email verification."""
    user = register_user(db, req.email, req.password, req.name)
    return {
        "success": True,
        "email": user.email,
        "email_verified": False,
        "message": "Kode verifikasi telah dikirim ke email Anda",
    }


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(request: Request, req: LoginRequest, db: Session = Depends(get_db)):
    """Login with email and password."""
    user = authenticate_user(db, req.email, req.password)
    token = create_access_token({"sub": str(user.id), "email": user.email})
    access_info = check_access(db, user)
    return TokenResponse(
        access_token=token,
        user={
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "is_admin": user.is_admin,
            "subscription": access_info,
        },
    )


# --- Email Verification & Password Reset ---

class VerifyEmailRequest(BaseModel):
    email: str
    otp: str


class ResendOtpRequest(BaseModel):
    email: str


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    email: str
    code: str
    new_password: str


@router.post("/verify-email")
@limiter.limit("5/minute")
async def verify_email(request: Request, req: VerifyEmailRequest, db: Session = Depends(get_db)):
    """Verify email with 6-digit OTP code."""
    user = db.query(User).filter(User.email == req.email.lower().strip()).first()
    if not user:
        raise HTTPException(status_code=404, detail="Email tidak ditemukan")
    if user.email_verified:
        return {"success": True, "message": "Email sudah terverifikasi"}
    if not user.otp_code or not user.otp_expires:
        raise HTTPException(status_code=400, detail="Kode OTP tidak valid. Silakan kirim ulang.")
    if datetime.utcnow() > user.otp_expires:
        raise HTTPException(status_code=400, detail="Kode OTP sudah kadaluarsa. Silakan kirim ulang.")
    if not verify_password(req.otp, user.otp_code):
        raise HTTPException(status_code=400, detail="Kode OTP salah")

    user.email_verified = True
    user.otp_code = None
    user.otp_expires = None
    db.commit()

    # Auto-login after verification
    token = create_access_token({"sub": str(user.id), "email": user.email})
    access_info = check_access(db, user)
    return {
        "success": True,
        "message": "Email berhasil diverifikasi",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "is_admin": user.is_admin,
            "subscription": access_info,
        },
    }


@router.post("/resend-otp")
@limiter.limit("3/minute")
async def resend_otp(request: Request, req: ResendOtpRequest, db: Session = Depends(get_db)):
    """Resend OTP to user's email."""
    from app.services.email_service import generate_otp, send_otp_email
    import threading

    user = db.query(User).filter(User.email == req.email.lower().strip()).first()
    if not user:
        raise HTTPException(status_code=404, detail="Email tidak ditemukan")
    if user.email_verified:
        return {"success": True, "message": "Email sudah terverifikasi"}

    otp = generate_otp()
    user.otp_code = hash_password(otp)
    user.otp_expires = datetime.utcnow() + timedelta(minutes=10)
    db.commit()

    threading.Thread(target=send_otp_email, args=(user.email, otp), daemon=True).start()
    return {"success": True, "message": "Kode verifikasi baru telah dikirim"}


@router.post("/forgot-password")
@limiter.limit("3/minute")
async def forgot_password(request: Request, req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Send password reset code to email."""
    from app.services.email_service import generate_otp, send_reset_email
    import threading

    user = db.query(User).filter(User.email == req.email.lower().strip()).first()
    # Always return success to prevent email enumeration
    if not user or not user.is_active:
        return {"success": True, "message": "Jika email terdaftar, kode reset telah dikirim"}

    code = generate_otp()
    user.reset_code = hash_password(code)
    user.reset_expires = datetime.utcnow() + timedelta(minutes=15)
    db.commit()

    threading.Thread(target=send_reset_email, args=(user.email, code), daemon=True).start()
    return {"success": True, "message": "Jika email terdaftar, kode reset telah dikirim"}


@router.post("/reset-password")
@limiter.limit("5/minute")
async def reset_password(request: Request, req: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset password with verification code."""
    user = db.query(User).filter(User.email == req.email.lower().strip()).first()
    if not user:
        raise HTTPException(status_code=400, detail="Kode reset tidak valid")
    if not user.reset_code or not user.reset_expires:
        raise HTTPException(status_code=400, detail="Kode reset tidak valid. Silakan minta ulang.")
    if datetime.utcnow() > user.reset_expires:
        raise HTTPException(status_code=400, detail="Kode reset sudah kadaluarsa")
    if not verify_password(req.code, user.reset_code):
        raise HTTPException(status_code=400, detail="Kode reset salah")
    if len(req.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password baru minimal 8 karakter")

    user.password_hash = hash_password(req.new_password)
    user.reset_code = None
    user.reset_expires = None
    user.email_verified = True  # Also verify email if it wasn't
    db.commit()
    return {"success": True, "message": "Password berhasil direset"}


@router.get("/me", response_model=UserResponse)
async def get_me(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current user profile + subscription status."""
    access_info = check_access(db, user)
    usage_count = get_usage_count(db, user.id)
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        is_admin=user.is_admin,
        created_at=user.created_at.isoformat(),
        avatar_color=user.avatar_color or "emerald",
        notify_usage_limit=user.notify_usage_limit if user.notify_usage_limit is not None else True,
        notify_expiry=user.notify_expiry if user.notify_expiry is not None else True,
        subscription=access_info,
        usage={
            "total": usage_count,
            "limit": FREE_USAGE_LIMIT if access_info["plan"] == "free" else None,
            "remaining": max(0, FREE_USAGE_LIMIT - usage_count) if access_info["plan"] == "free" else None,
        },
    )


# --- Profile Update ---

class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    avatar_color: Optional[str] = None
    notify_usage_limit: Optional[bool] = None
    notify_expiry: Optional[bool] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class DeleteAccountRequest(BaseModel):
    password: str


@router.patch("/profile")
async def update_profile(
    req: UpdateProfileRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update user profile (name, avatar color, notification preferences)."""
    if req.name is not None:
        user.name = req.name.strip()
    if req.avatar_color is not None:
        VALID_COLORS = ["emerald", "blue", "purple", "rose", "amber", "cyan", "indigo", "slate"]
        if req.avatar_color in VALID_COLORS:
            user.avatar_color = req.avatar_color
    if req.notify_usage_limit is not None:
        user.notify_usage_limit = req.notify_usage_limit
    if req.notify_expiry is not None:
        user.notify_expiry = req.notify_expiry
    db.commit()
    db.refresh(user)
    return {
        "success": True,
        "name": user.name,
        "avatar_color": user.avatar_color,
        "notify_usage_limit": user.notify_usage_limit,
        "notify_expiry": user.notify_expiry,
    }


@router.post("/change-password")
async def change_password(
    req: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change user password (requires current password)."""
    if not verify_password(req.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Password saat ini salah")
    if len(req.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password baru minimal 8 karakter")
    user.password_hash = hash_password(req.new_password)
    db.commit()
    return {"success": True, "message": "Password berhasil diubah"}


# --- Activity Log ---

@router.get("/activity")
async def get_activity(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get last 20 usage log entries for the current user."""
    from app.models.user import UsageLog
    logs = (
        db.query(UsageLog)
        .filter(UsageLog.user_id == user.id)
        .order_by(UsageLog.created_at.desc())
        .limit(20)
        .all()
    )
    return {
        "activities": [
            {
                "id": log.id,
                "action": log.action,
                "count": log.count,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ]
    }


# --- Account Deletion ---

@router.delete("/account")
async def delete_account(
    req: DeleteAccountRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Deactivate user account. Requires password confirmation."""
    if not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Password salah")
    user.is_active = False
    user.password_hash = ""  # Clear password
    db.commit()
    return {"success": True, "message": "Akun berhasil dihapus"}


# --- Phone Verification ---

class SendPhoneOtpRequest(BaseModel):
    phone_number: str


class VerifyPhoneRequest(BaseModel):
    phone_number: str
    otp: str


class ActivateTrialRequest(BaseModel):
    phone_number: str
    otp: str


@router.post("/send-phone-otp")
@limiter.limit("3/minute")
async def send_phone_otp(
    request: Request,
    req: SendPhoneOtpRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Send OTP to user's WhatsApp for phone verification."""
    from app.services.whatsapp_service import generate_otp, send_whatsapp_otp, create_otp_expiry

    phone = req.phone_number.strip()

    # Check if phone already used by another user
    existing = db.query(User).filter(
        User.phone_number == phone,
        User.id != user.id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Nomor WhatsApp sudah digunakan akun lain")

    # Generate and store OTP
    otp = generate_otp()
    user.phone_number = phone
    user.phone_otp_code = hash_password(otp)
    user.phone_otp_expires = create_otp_expiry()
    db.commit()

    # Send via WhatsApp
    success, message = send_whatsapp_otp(phone, otp)
    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {"success": True, "message": message}


@router.post("/verify-phone")
async def verify_phone(
    req: VerifyPhoneRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Verify phone number with OTP."""
    if not user.phone_otp_code or not user.phone_otp_expires:
        raise HTTPException(status_code=400, detail="Kode OTP tidak ditemukan. Silakan minta kode baru.")

    if user.phone_number != req.phone_number.strip():
        raise HTTPException(status_code=400, detail="Nomor telepon tidak sesuai")

    if datetime.utcnow() > user.phone_otp_expires:
        raise HTTPException(status_code=400, detail="Kode OTP sudah kedaluwarsa. Silakan minta kode baru.")

    if not verify_password(req.otp, user.phone_otp_code):
        raise HTTPException(status_code=400, detail="Kode OTP salah")

    # Mark phone as verified
    user.phone_verified = True
    user.phone_otp_code = None
    user.phone_otp_expires = None
    db.commit()

    return {"success": True, "message": "Nomor WhatsApp berhasil diverifikasi"}

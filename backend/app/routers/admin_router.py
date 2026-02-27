"""
Admin Router — /admin/*
Provides admin-only endpoints for user management, system stats, and configuration.
"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.auth import require_admin, activate_pro, hash_password
from app.models.user import User, Subscription, UsageLog, PlanType, SubscriptionStatus

router = APIRouter(prefix="/admin", tags=["Admin"])


# --- Schemas ---

class UserListItem(BaseModel):
    id: int
    email: str
    name: str
    is_active: bool
    is_admin: bool
    created_at: str
    plan: Optional[str] = None
    status: Optional[str] = None
    usage_count: int = 0


class UserListResponse(BaseModel):
    total: int
    users: List[UserListItem]


class SystemStatsResponse(BaseModel):
    total_users: int
    active_users: int
    admin_users: int
    pro_users: int
    free_users: int
    total_scans: int


class SetAdminRequest(BaseModel):
    is_admin: bool


class SetActiveRequest(BaseModel):
    is_active: bool


class SetPlanRequest(BaseModel):
    plan: str  # "free" or "pro"


# --- Endpoints ---

@router.get("/users", response_model=UserListResponse)
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    search: Optional[str] = None,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List all users with pagination + search."""
    query = db.query(User)
    if search:
        query = query.filter(
            User.email.ilike(f"%{search}%") | User.name.ilike(f"%{search}%")
        )
    total = query.count()
    users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()

    items = []
    for u in users:
        usage = db.query(func.sum(UsageLog.count)).filter(UsageLog.user_id == u.id).scalar() or 0
        sub = u.subscription
        items.append(UserListItem(
            id=u.id,
            email=u.email,
            name=u.name,
            is_active=u.is_active,
            is_admin=u.is_admin,
            created_at=u.created_at.isoformat(),
            plan=sub.plan if sub else None,
            status=sub.status if sub else None,
            usage_count=usage,
        ))

    return UserListResponse(total=total, users=items)


@router.get("/stats", response_model=SystemStatsResponse)
async def system_stats(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get system-wide statistics."""
    total = db.query(User).count()
    active = db.query(User).filter(User.is_active == True).count()
    admins = db.query(User).filter(User.is_admin == True).count()
    pro = db.query(Subscription).filter(Subscription.plan == PlanType.PRO).count()
    free = total - pro
    scans = db.query(func.sum(UsageLog.count)).scalar() or 0

    return SystemStatsResponse(
        total_users=total,
        active_users=active,
        admin_users=admins,
        pro_users=pro,
        free_users=free,
        total_scans=scans,
    )


@router.patch("/users/{user_id}/admin")
async def set_admin_status(
    user_id: int,
    req: SetAdminRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Grant or revoke admin privileges."""
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")
    if target.id == admin.id and not req.is_admin:
        raise HTTPException(status_code=400, detail="Tidak bisa menghapus admin diri sendiri")

    target.is_admin = req.is_admin
    db.commit()
    return {"success": True, "user_id": user_id, "is_admin": req.is_admin}


@router.patch("/users/{user_id}/active")
async def set_active_status(
    user_id: int,
    req: SetActiveRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Activate or deactivate a user account."""
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")
    if target.id == admin.id:
        raise HTTPException(status_code=400, detail="Tidak bisa menonaktifkan diri sendiri")

    target.is_active = req.is_active
    db.commit()
    return {"success": True, "user_id": user_id, "is_active": req.is_active}


@router.patch("/users/{user_id}/plan")
async def set_user_plan(
    user_id: int,
    req: SetPlanRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Manually set a user's plan (free/pro)."""
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")

    if req.plan == "pro":
        activate_pro(db, target, payment_ref="admin_override")
        return {"success": True, "user_id": user_id, "plan": "pro"}
    elif req.plan == "free":
        sub = target.subscription
        if sub:
            sub.plan = PlanType.FREE
            sub.status = SubscriptionStatus.EXPIRED
            db.commit()
        return {"success": True, "user_id": user_id, "plan": "free"}
    else:
        raise HTTPException(status_code=400, detail="Plan harus 'free' atau 'pro'")


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Permanently delete a user and all their data."""
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")
    if target.id == admin.id:
        raise HTTPException(status_code=400, detail="Tidak bisa menghapus diri sendiri")

    db.query(UsageLog).filter(UsageLog.user_id == user_id).delete()
    db.query(Subscription).filter(Subscription.user_id == user_id).delete()
    db.query(User).filter(User.id == user_id).delete()
    db.commit()
    return {"success": True, "deleted_user_id": user_id}

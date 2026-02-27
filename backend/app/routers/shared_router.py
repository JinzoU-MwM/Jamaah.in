"""
Shared Router — Mutawwif Mobile Manifest.

Provides a secure, PIN-protected, read-only public link for Mutawwif
(tour leaders) to view their group's manifest on mobile.

Two endpoints:
- POST /groups/{group_id}/share  (JWT + Pro)  → generate/update share link
- POST /shared/manifest/{token}  (PUBLIC)     → PIN-verified read-only manifest
"""
import os
import uuid
import logging
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user, check_access
from app.models.user import User
from app.models.group import Group, GroupMember
from app.models.operational import Room

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Shared Manifest"])

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


# =============================================================================
# PRO PLAN DEPENDENCY (same pattern as inventory_router)
# =============================================================================

async def require_pro_plan(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    """Require active Pro subscription."""
    access = check_access(db, user)

    if access["plan"] != "pro":
        raise HTTPException(
            status_code=403,
            detail="Fitur ini hanya untuk pengguna Pro. Upgrade ke Pro untuk mengakses."
        )

    if access["status"] != "active":
        raise HTTPException(
            status_code=403,
            detail=f"Langganan Pro tidak aktif. Status: {access['status']}"
        )

    return user


# =============================================================================
# SCHEMAS
# =============================================================================

class ShareGroupRequest(BaseModel):
    pin: str = Field(..., min_length=4, max_length=6, description="4-6 digit PIN")
    expires_in_days: int = Field(default=30, ge=1, le=365, description="Link expiry in days")


class ShareGroupResponse(BaseModel):
    shared_token: str
    shared_url: str
    pin: str
    expires_at: str
    group_name: str


class ManifestPinRequest(BaseModel):
    pin: str = Field(..., min_length=4, max_length=6)


class MutawwifMemberResponse(BaseModel):
    """Privacy-safe member response — NO NIK, NO address, NO full personal data."""
    id: int
    nama: str
    title: str              # Mr/Mrs/Ms — for gender identification
    no_paspor: str
    no_hp: str
    baju_size: str
    room_number: Optional[str] = None
    room_id: Optional[int] = None
    is_equipment_received: bool = False


class ManifestResponse(BaseModel):
    group_name: str
    total_members: int
    members: List[MutawwifMemberResponse]


# =============================================================================
# ENDPOINT 1: Generate/Update Share Link (Protected — JWT + Pro)
# =============================================================================

@router.post("/groups/{group_id}/share")
async def share_group(
    group_id: int,
    body: ShareGroupRequest,
    user: User = Depends(require_pro_plan),
    db: Session = Depends(get_db),
):
    """
    Generate or update a PIN-protected public manifest link for this group.
    Only group owner with active Pro plan can call this.
    """
    # Verify ownership
    group = db.query(Group).filter(
        Group.id == group_id,
        Group.user_id == user.id
    ).first()

    if not group:
        raise HTTPException(status_code=404, detail="Grup tidak ditemukan")

    # Validate PIN is numeric
    if not body.pin.isdigit():
        raise HTTPException(status_code=400, detail="PIN harus berupa angka")

    # Generate or reuse token
    if not group.shared_token:
        group.shared_token = uuid.uuid4().hex  # 32-char hex string

    group.shared_pin = body.pin
    group.shared_expires_at = datetime.utcnow() + timedelta(days=body.expires_in_days)

    db.commit()
    db.refresh(group)

    shared_url = f"{FRONTEND_URL}/#/m/{group.shared_token}"

    logger.info(f"User {user.id} shared group {group_id} with token {group.shared_token[:8]}...")

    return ShareGroupResponse(
        shared_token=group.shared_token,
        shared_url=shared_url,
        pin=group.shared_pin,
        expires_at=group.shared_expires_at.isoformat(),
        group_name=group.name
    )


# =============================================================================
# ENDPOINT 2: Public Manifest Access (No Auth — PIN-protected)
# =============================================================================

@router.post("/shared/manifest/{shared_token}")
async def get_shared_manifest(
    shared_token: str,
    body: ManifestPinRequest,
    db: Session = Depends(get_db),
):
    """
    PUBLIC endpoint — no JWT required.
    Verify PIN + token, return privacy-safe member list.
    """
    # Find group by token
    group = db.query(Group).filter(
        Group.shared_token == shared_token
    ).first()

    if not group:
        raise HTTPException(status_code=404, detail="Link tidak ditemukan atau sudah kedaluwarsa")

    # Check expiry
    if group.shared_expires_at and group.shared_expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=401,
            detail="Link sudah kedaluwarsa. Hubungi admin untuk memperpanjang."
        )

    # Verify PIN
    if not group.shared_pin or body.pin != group.shared_pin:
        raise HTTPException(status_code=401, detail="PIN salah")

    # Fetch members with room info
    members = db.query(GroupMember).filter(
        GroupMember.group_id == group.id
    ).order_by(GroupMember.nama).all()

    # Build privacy-safe response
    member_list = []
    for m in members:
        # Get room number if assigned
        room_number = None
        if m.room_id:
            room = db.query(Room).filter(Room.id == m.room_id).first()
            if room:
                room_number = room.room_number

        member_list.append(MutawwifMemberResponse(
            id=m.id,
            nama=m.nama or "",
            title=m.title or "",
            no_paspor=m.no_paspor or "",
            no_hp=m.no_hp or "",
            baju_size=m.baju_size or "",
            room_number=room_number,
            room_id=m.room_id,
            is_equipment_received=m.is_equipment_received or False,
        ))

    logger.info(f"Manifest accessed for group {group.id} ({len(member_list)} members)")

    return ManifestResponse(
        group_name=group.name,
        total_members=len(member_list),
        members=member_list
    )


# =============================================================================
# ENDPOINT 3: Revoke Share Link (Protected — JWT + Pro)
# =============================================================================

@router.delete("/groups/{group_id}/share")
async def revoke_share(
    group_id: int,
    user: User = Depends(require_pro_plan),
    db: Session = Depends(get_db),
):
    """Revoke the shared manifest link for a group."""
    group = db.query(Group).filter(
        Group.id == group_id,
        Group.user_id == user.id
    ).first()

    if not group:
        raise HTTPException(status_code=404, detail="Grup tidak ditemukan")

    group.shared_token = None
    group.shared_pin = None
    group.shared_expires_at = None

    db.commit()

    logger.info(f"User {user.id} revoked share for group {group_id}")

    return {"status": "revoked", "group_id": group_id}

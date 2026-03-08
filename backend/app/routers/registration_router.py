"""
Registration Router — Self-service jamaah onboarding via registration links.
"""
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, Form, UploadFile, File
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
import os

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

from app.database import get_db
from app.auth import get_current_user
from app.models.user import User
from app.models.group import Group, GroupMember
from app.models.registration import RegistrationLink
from app.models.pending_member import PendingMember
from pydantic import BaseModel
from app.config import MAX_FILE_SIZE, ALLOWED_EXTENSIONS

router = APIRouter(prefix="/registration", tags=["registration"])


# --- Schemas ---
class GenerateLinkRequest(BaseModel):
    group_id: int
    expires_in_days: int = 30


class GenerateLinkResponse(BaseModel):
    link: str
    token: str
    expires_at: str


# --- Admin Endpoints ---
@router.post("/generate", response_model=GenerateLinkResponse)
def generate_link(
    req: GenerateLinkRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate a registration link for a group."""
    group = db.query(Group).filter(Group.id == req.group_id).first()
    if not group:
        raise HTTPException(404, "Group not found")

    # Check ownership
    if group.user_id != current_user.id:
        raise HTTPException(403, "Not authorized")

    # Generate token
    token = RegistrationLink.generate_token()
    expires_at = datetime.utcnow() + timedelta(days=req.expires_in_days)

    link = RegistrationLink(
        group_id=req.group_id,
        token=token,
        expires_at=expires_at,
        created_by=current_user.id,
    )
    db.add(link)
    db.commit()

    return GenerateLinkResponse(
        link=f"{FRONTEND_URL}/#/reg/{token}",
        token=token,
        expires_at=expires_at.isoformat(),
    )


@router.get("/link/{group_id}")
def get_link_info(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get registration link info for a group."""
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(404, "Group not found")
    if group.user_id != current_user.id:
        raise HTTPException(403, "Not authorized")

    link = (
        db.query(RegistrationLink)
        .filter(
            RegistrationLink.group_id == group_id,
            RegistrationLink.is_active == True,
        )
        .first()
    )

    if not link:
        return {"active": False}

    return {
        "active": True,
        "token": link.token,
        "link": f"{FRONTEND_URL}/#/reg/{link.token}",
        "expires_at": link.expires_at.isoformat(),
        "is_expired": datetime.utcnow() > link.expires_at,
    }


@router.delete("/link/{group_id}")
def revoke_link(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Revoke registration link."""
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(404, "Group not found")
    if group.user_id != current_user.id:
        raise HTTPException(403, "Not authorized")

    link = (
        db.query(RegistrationLink)
        .filter(
            RegistrationLink.group_id == group_id,
            RegistrationLink.is_active == True,
        )
        .first()
    )

    if link:
        link.is_active = False
        db.commit()

    return {"success": True}


# --- Public Endpoints ---
@router.get("/public/{token}")
def get_registration_info(token: str, db: Session = Depends(get_db)):
    """Get registration page info."""
    link = (
        db.query(RegistrationLink)
        .filter(
            RegistrationLink.token == token,
            RegistrationLink.is_active == True,
        )
        .first()
    )

    if not link:
        raise HTTPException(404, "Registration link not found")

    if datetime.utcnow() > link.expires_at:
        raise HTTPException(410, "Registration link has expired")

    group = db.query(Group).filter(Group.id == link.group_id).first()

    return {
        "group_name": group.name,
        "group_id": group.id,
        "expires_at": link.expires_at.isoformat(),
    }


@router.post("/public/{token}")
async def submit_registration(
    token: str,
    phone_number: str = Form(...),
    ktp: UploadFile | None = File(None),
    passport: UploadFile | None = File(None),
    visa: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    """Submit registration data via multipart form."""
    link = (
        db.query(RegistrationLink)
        .filter(
            RegistrationLink.token == token,
            RegistrationLink.is_active == True,
        )
        .first()
    )

    if not link:
        raise HTTPException(404, "Registration link not found")

    if datetime.utcnow() > link.expires_at:
        raise HTTPException(410, "Registration link has expired")

    for field_name, upload in (("ktp", ktp), ("passport", passport), ("visa", visa)):
        if not upload:
            continue
        ext = Path(upload.filename or "").suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(400, f"Invalid {field_name} file type")
        content = await upload.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(400, f"{field_name} file too large")

    # Check for duplicate phone number
    existing = (
        db.query(PendingMember)
        .filter(
            PendingMember.group_id == link.group_id,
            PendingMember.phone_number == phone_number,
        )
        .first()
    )

    if existing:
        raise HTTPException(400, "This phone number has already registered")

    # Create pending member
    pending = PendingMember(
        group_id=link.group_id,
        phone_number=phone_number,
        status="pending",
    )
    db.add(pending)
    db.commit()

    return {
        "success": True,
        "message": "Data berhasil dikirim, menunggu review",
        "pending_id": pending.id,
    }


# --- Pending Members Review ---
@router.get("/pending/{group_id}")
def list_pending(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List pending members for review."""
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group or group.user_id != current_user.id:
        raise HTTPException(403, "Not authorized")

    pending = (
        db.query(PendingMember)
        .filter(
            PendingMember.group_id == group_id,
            PendingMember.status == "pending",
        )
        .all()
    )

    return {
        "pending": [
            {
                "id": p.id,
                "phone_number": p.phone_number,
                "submitted_at": p.submitted_at.isoformat(),
                "nama": p.nama,
                "no_identitas": p.no_identitas,
                "no_paspor": p.no_paspor,
            }
            for p in pending
        ]
    }


@router.post("/pending/{pending_id}/approve")
def approve_pending(
    pending_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Approve a pending member."""
    pending = (
        db.query(PendingMember).filter(PendingMember.id == pending_id).first()
    )
    if not pending:
        raise HTTPException(404, "Pending member not found")

    group = db.query(Group).filter(Group.id == pending.group_id).first()
    if group.user_id != current_user.id:
        raise HTTPException(403, "Not authorized")

    # Create GroupMember from PendingMember
    member = GroupMember(
        group_id=pending.group_id,
        title=pending.title,
        nama=pending.nama,
        nama_ayah=pending.nama_ayah,
        jenis_identitas=pending.jenis_identitas,
        no_identitas=pending.no_identitas,
        nama_paspor=pending.nama_paspor,
        no_paspor=pending.no_paspor,
        tanggal_paspor=pending.tanggal_paspor,
        kota_paspor=pending.kota_paspor,
        tempat_lahir=pending.tempat_lahir,
        tanggal_lahir=pending.tanggal_lahir,
        alamat=pending.alamat,
        provinsi=pending.provinsi,
        kabupaten=pending.kabupaten,
        kecamatan=pending.kecamatan,
        kelurahan=pending.kelurahan,
        no_telepon=pending.no_telepon or pending.phone_number,
        no_hp=pending.no_hp,
        kewarganegaraan=pending.kewarganegaraan,
        status_pernikahan=pending.status_pernikahan,
        pendidikan=pending.pendidikan,
        pekerjaan=pending.pekerjaan,
        provider_visa=pending.provider_visa,
        no_visa=pending.no_visa,
        tanggal_visa=pending.tanggal_visa,
        tanggal_visa_akhir=pending.tanggal_visa_akhir,
        asuransi=pending.asuransi,
        no_polis=pending.no_polis,
        tanggal_input_polis=pending.tanggal_input_polis,
        tanggal_awal_polis=pending.tanggal_awal_polis,
        tanggal_akhir_polis=pending.tanggal_akhir_polis,
        no_bpjs=pending.no_bpjs,
    )
    db.add(member)

    # Update pending status
    pending.status = "approved"
    pending.reviewed_at = datetime.utcnow()
    pending.reviewed_by = current_user.id

    db.commit()

    return {"success": True, "member_id": member.id}


@router.post("/pending/{pending_id}/reject")
def reject_pending(
    pending_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reject a pending member."""
    pending = (
        db.query(PendingMember).filter(PendingMember.id == pending_id).first()
    )
    if not pending:
        raise HTTPException(404, "Pending member not found")

    group = db.query(Group).filter(Group.id == pending.group_id).first()
    if group.user_id != current_user.id:
        raise HTTPException(403, "Not authorized")

    pending.status = "rejected"
    pending.reviewed_at = datetime.utcnow()
    pending.reviewed_by = current_user.id
    db.commit()

    return {"success": True}

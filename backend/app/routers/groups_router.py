"""
Groups Router — CRUD for groups + member management.
Lets users organize jamaah data into named groups/trips.
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import func

from app.database import get_db
from app.auth import get_current_user, check_access
from app.models.user import User
from app.models.group import Group, GroupMember
from app.models.team import TeamMember, MemberStatus
from sqlalchemy import or_

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/groups", tags=["Groups"])

# --- Free tier limit ---
MAX_GROUPS_FREE = 2


# =============================================================================
# SCHEMAS
# =============================================================================

class GroupCreate(BaseModel):
    name: str
    description: str = ""

class GroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class MemberData(BaseModel):
    """A single jamaah row — matches ExtractedDataItem fields."""
    title: str = ""
    nama: str = ""
    nama_ayah: str = ""
    jenis_identitas: str = ""
    no_identitas: str = ""
    nama_paspor: str = ""
    no_paspor: str = ""
    tanggal_paspor: str = ""
    kota_paspor: str = ""
    tempat_lahir: str = ""
    tanggal_lahir: str = ""
    alamat: str = ""
    provinsi: str = ""
    kabupaten: str = ""
    kecamatan: str = ""
    kelurahan: str = ""
    no_telepon: str = ""
    no_hp: str = ""
    kewarganegaraan: str = "WNI"
    status_pernikahan: str = ""
    pendidikan: str = ""
    pekerjaan: str = ""
    provider_visa: str = ""
    no_visa: str = ""
    tanggal_visa: str = ""
    tanggal_visa_akhir: str = ""
    asuransi: str = ""
    no_polis: str = ""
    tanggal_input_polis: str = ""
    tanggal_awal_polis: str = ""
    tanggal_akhir_polis: str = ""
    no_bpjs: str = ""

class AddMembersRequest(BaseModel):
    members: List[MemberData]


# =============================================================================
# HELPERS
# =============================================================================

def _get_user_org_id(db: Session, user_id: int):
    """Get the org ID the user belongs to (if any)."""
    membership = db.query(TeamMember).filter(
        TeamMember.user_id == user_id,
        TeamMember.status == MemberStatus.ACTIVE
    ).first()
    return membership.org_id if membership else None


def _get_user_group(db: Session, user: User, group_id: int) -> Group:
    """Get a group owned by the user or in the user's organization, or raise 404."""
    org_id = _get_user_org_id(db, user.id)
    filters = [Group.id == group_id]
    if org_id:
        filters.append(or_(Group.user_id == user.id, Group.org_id == org_id))
    else:
        filters.append(Group.user_id == user.id)
    group = db.query(Group).filter(*filters).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group


def _group_to_dict(group: Group, member_count: int = None) -> dict:
    """Serialize a group for the API response."""
    return {
        "id": group.id,
        "name": group.name,
        "description": group.description or "",
        "member_count": member_count if member_count is not None else len(group.members),
        "created_at": group.created_at.isoformat() if group.created_at else None,
        "updated_at": group.updated_at.isoformat() if group.updated_at else None,
    }


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/")
async def list_groups(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all groups owned by the current user + team groups."""
    org_id = _get_user_org_id(db, user.id)

    # Use SQL COUNT subquery to avoid loading all members just for counting
    member_count_sq = (
        db.query(GroupMember.group_id, func.count(GroupMember.id).label("cnt"))
        .group_by(GroupMember.group_id)
        .subquery()
    )

    query = (
        db.query(Group, func.coalesce(member_count_sq.c.cnt, 0))
        .outerjoin(member_count_sq, Group.id == member_count_sq.c.group_id)
    )

    if org_id:
        query = query.filter(or_(Group.user_id == user.id, Group.org_id == org_id))
    else:
        query = query.filter(Group.user_id == user.id)

    rows = query.order_by(Group.updated_at.desc()).all()
    return {
        "groups": [_group_to_dict(g, cnt) for g, cnt in rows],
        "total": len(rows),
    }


@router.post("/", status_code=201)
async def create_group(
    body: GroupCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new group. Free users limited to 3 groups."""
    # Check free tier limit
    access = check_access(db, user)
    if access["plan"] != "pro":
        count = db.query(Group).filter(Group.user_id == user.id).count()
        if count >= MAX_GROUPS_FREE:
            raise HTTPException(
                status_code=403,
                detail=f"Pengguna gratis maksimal {MAX_GROUPS_FREE} grup. Upgrade ke Pro untuk grup unlimited.",
            )

    if not body.name or not body.name.strip():
        raise HTTPException(status_code=400, detail="Nama grup tidak boleh kosong")

    group = Group(
        user_id=user.id,
        name=body.name.strip(),
        description=body.description.strip() if body.description else "",
    )
    db.add(group)
    db.commit()
    db.refresh(group)

    logger.info(f"User {user.email} created group '{group.name}' (id={group.id})")
    return _group_to_dict(group)


@router.get("/{group_id}")
async def get_group(
    group_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a group with all its members."""
    org_id = _get_user_org_id(db, user.id)
    filters = [Group.id == group_id]
    if org_id:
        filters.append(or_(Group.user_id == user.id, Group.org_id == org_id))
    else:
        filters.append(Group.user_id == user.id)
    group = (
        db.query(Group)
        .options(joinedload(Group.members), selectinload(Group.rooms))
        .filter(*filters)
        .first()
    )
    if not group:
        raise HTTPException(status_code=404, detail="Grup tidak ditemukan")
    return {
        **_group_to_dict(group, len(group.members)),
        "members": [m.to_dict() for m in group.members],
    }


@router.put("/{group_id}")
async def update_group(
    group_id: int,
    body: GroupUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update group name/description."""
    group = _get_user_group(db, user, group_id)

    if body.name is not None:
        if not body.name.strip():
            raise HTTPException(status_code=400, detail="Nama grup tidak boleh kosong")
        group.name = body.name.strip()
    if body.description is not None:
        group.description = body.description.strip()

    db.commit()
    db.refresh(group)
    return _group_to_dict(group)


@router.delete("/{group_id}")
async def delete_group(
    group_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a group and all its members (cascade)."""
    group = _get_user_group(db, user, group_id)
    group_name = group.name
    db.delete(group)
    db.commit()
    logger.info(f"User {user.email} deleted group '{group_name}' (id={group_id})")
    return {"status": "deleted", "id": group_id}


@router.post("/{group_id}/members")
async def add_members(
    group_id: int,
    body: AddMembersRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add member rows to a group (from OCR results or manual entry)."""
    group = _get_user_group(db, user, group_id)

    if not body.members:
        raise HTTPException(status_code=400, detail="No members provided")

    added = []
    for m in body.members:
        member = GroupMember(
            group_id=group.id,
            **m.model_dump(),
        )
        db.add(member)
        added.append(member)

    db.commit()

    # Refresh to get IDs
    for member in added:
        db.refresh(member)

    logger.info(f"Added {len(added)} members to group '{group.name}' (id={group.id})")
    return {
        "status": "added",
        "count": len(added),
        "members": [m.to_dict() for m in added],
    }


@router.put("/{group_id}/members/{member_id}")
async def update_member(
    group_id: int,
    member_id: int,
    body: MemberData,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a single member row."""
    group = _get_user_group(db, user, group_id)
    member = db.query(GroupMember).filter(
        GroupMember.id == member_id, GroupMember.group_id == group.id
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    update_data = body.model_dump()
    for key, value in update_data.items():
        setattr(member, key, value)

    db.commit()
    db.refresh(member)
    return member.to_dict()


@router.delete("/{group_id}/members/{member_id}")
async def delete_member(
    group_id: int,
    member_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove a member row from a group."""
    group = _get_user_group(db, user, group_id)
    member = db.query(GroupMember).filter(
        GroupMember.id == member_id, GroupMember.group_id == group.id
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    db.delete(member)
    db.commit()
    return {"status": "deleted", "id": member_id}

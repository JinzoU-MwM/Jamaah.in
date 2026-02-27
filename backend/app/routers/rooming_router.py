"""
Rooming Router — Hotel Room Allocation API.

Pro-only endpoints for auto-rooming and manual room management.
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user, check_access
from app.models.user import User, PlanType
from app.models.group import Group, GroupMember
from app.models.operational import Room, RoomType, GenderType
from app.services import rooming_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rooming", tags=["Rooming (Pro)"])


# =============================================================================
# PRO PLAN DEPENDENCY
# =============================================================================

async def require_pro_plan(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    """FastAPI dependency: require active Pro subscription."""
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


def _get_user_group(db: Session, user: User, group_id: int) -> Group:
    """Get a group owned by the user, or raise 404."""
    group = db.query(Group).filter(Group.id == group_id, Group.user_id == user.id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Grup tidak ditemukan")
    return group


# =============================================================================
# SCHEMAS
# =============================================================================

class RoomCreate(BaseModel):
    room_number: str
    room_type: str = RoomType.QUAD      # quad/triple/double
    gender_type: str = GenderType.MALE  # male/female/family
    capacity: Optional[int] = None

class AssignMemberRequest(BaseModel):
    member_id: int
    room_id: int

class AutoRoomingRequest(BaseModel):
    room_capacity: int = 4  # Default quad room


# =============================================================================
# ROOM CRUD ENDPOINTS
# =============================================================================

@router.get("/group/{group_id}")
async def list_group_rooms(
    group_id: int,
    user: User = Depends(require_pro_plan),
    db: Session = Depends(get_db),
):
    """List all rooms for a group with member assignments."""
    _get_user_group(db, user, group_id)
    rooms = rooming_service.get_group_rooms(db, group_id)
    return {"group_id": group_id, "rooms": rooms, "total": len(rooms)}


@router.post("/group/{group_id}", status_code=201)
async def create_room(
    group_id: int,
    body: RoomCreate,
    user: User = Depends(require_pro_plan),
    db: Session = Depends(get_db),
):
    """Create a new room for a group."""
    _get_user_group(db, user, group_id)
    
    # Validate room type
    valid_room_types = [RoomType.QUAD, RoomType.TRIPLE, RoomType.DOUBLE]
    if body.room_type not in valid_room_types:
        raise HTTPException(
            status_code=400,
            detail=f"Tipe kamar tidak valid. Pilih: {', '.join(valid_room_types)}"
        )
    
    # Validate gender type
    valid_gender_types = [GenderType.MALE, GenderType.FEMALE, GenderType.FAMILY]
    if body.gender_type not in valid_gender_types:
        raise HTTPException(
            status_code=400,
            detail=f"Tipe gender tidak valid. Pilih: {', '.join(valid_gender_types)}"
        )
    
    room = rooming_service.create_room(
        db, group_id, body.room_number, body.room_type, body.gender_type, body.capacity
    )
    return room.to_dict()


@router.get("/{room_id}")
async def get_room(
    room_id: int,
    user: User = Depends(require_pro_plan),
    db: Session = Depends(get_db),
):
    """Get room details with assigned members."""
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Kamar tidak ditemukan")
    
    # Verify ownership through group
    _get_user_group(db, user, room.group_id)
    
    return room.to_dict()


@router.delete("/{room_id}")
async def delete_room(
    room_id: int,
    user: User = Depends(require_pro_plan),
    db: Session = Depends(get_db),
):
    """Delete a room (unassigns all members)."""
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Kamar tidak ditemukan")
    
    # Verify ownership through group
    _get_user_group(db, user, room.group_id)
    
    rooming_service.delete_room(db, room_id)
    return {"status": "deleted", "id": room_id}


# =============================================================================
# MEMBER ASSIGNMENT ENDPOINTS
# =============================================================================

@router.post("/assign")
async def assign_member(
    body: AssignMemberRequest,
    user: User = Depends(require_pro_plan),
    db: Session = Depends(get_db),
):
    """Manually assign a member to a room."""
    member = db.query(GroupMember).filter(GroupMember.id == body.member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member tidak ditemukan")
    
    room = db.query(Room).filter(Room.id == body.room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Kamar tidak ditemukan")
    
    # Verify ownership
    _get_user_group(db, user, member.group_id)
    _get_user_group(db, user, room.group_id)
    
    try:
        member = rooming_service.assign_member_to_room(db, body.member_id, body.room_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return member.to_dict_full()


@router.post("/unassign/{member_id}")
async def unassign_member(
    member_id: int,
    user: User = Depends(require_pro_plan),
    db: Session = Depends(get_db),
):
    """Remove a member from their room."""
    member = db.query(GroupMember).filter(GroupMember.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member tidak ditemukan")
    
    # Verify ownership
    _get_user_group(db, user, member.group_id)
    
    member = rooming_service.unassign_member_from_room(db, member_id)
    return member.to_dict_full()


# =============================================================================
# AUTO-ROOMING ENDPOINTS
# =============================================================================

@router.post("/auto/{group_id}")
async def auto_rooming(
    group_id: int,
    body: AutoRoomingRequest = None,
    user: User = Depends(require_pro_plan),
    db: Session = Depends(get_db),
):
    """
    Automatically assign pilgrims to hotel rooms.
    
    Algorithm:
    - Families (same family_id) are placed together
    - Remaining males grouped in male-only rooms
    - Remaining females grouped in female-only rooms
    - No mixing unless family
    """
    _get_user_group(db, user, group_id)
    
    if body is None:
        body = AutoRoomingRequest()
    
    result = rooming_service.generate_auto_rooming(db, group_id, body.room_capacity)
    
    return {
        "status": "success",
        "group_id": group_id,
        **result
    }


@router.delete("/auto/{group_id}")
async def clear_auto_rooming(
    group_id: int,
    user: User = Depends(require_pro_plan),
    db: Session = Depends(get_db),
):
    """Clear all auto-assigned rooms (for re-running auto-rooming)."""
    _get_user_group(db, user, group_id)
    
    updated = rooming_service.clear_room_assignments(db, group_id)
    
    return {
        "status": "cleared",
        "group_id": group_id,
        "members_unassigned": updated
    }


# =============================================================================
# SUMMARY ENDPOINTS
# =============================================================================

@router.get("/summary/{group_id}")
async def get_rooming_summary(
    group_id: int,
    user: User = Depends(require_pro_plan),
    db: Session = Depends(get_db),
):
    """Get a summary of room assignments for a group."""
    _get_user_group(db, user, group_id)
    
    summary = rooming_service.get_rooming_summary(db, group_id)
    return summary

"""
Itinerary Router — CRUD for trip schedule/itinerary items.
"""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.auth import get_current_user
from app.models.user import User
from app.models.group import Group
from app.models.itinerary import Itinerary
from app.models.team import TeamMember, MemberStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/itineraries", tags=["Itineraries"])


# =============================================================================
# SCHEMAS
# =============================================================================

class ItineraryCreate(BaseModel):
    date: str
    time_start: str = ""
    time_end: str = ""
    activity: str
    location: str = ""
    notes: str = ""
    category: str = "activity"

class ItineraryUpdate(BaseModel):
    date: Optional[str] = None
    time_start: Optional[str] = None
    time_end: Optional[str] = None
    activity: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    category: Optional[str] = None


# =============================================================================
# HELPERS
# =============================================================================

def _get_accessible_group(db: Session, user: User, group_id: int) -> Group:
    """Get a group the user owns or belongs to via org, or raise 404."""
    membership = db.query(TeamMember).filter(
        TeamMember.user_id == user.id,
        TeamMember.status == MemberStatus.ACTIVE,
    ).first()
    org_id = membership.org_id if membership else None

    filters = [Group.id == group_id]
    if org_id:
        filters.append(or_(Group.user_id == user.id, Group.org_id == org_id))
    else:
        filters.append(Group.user_id == user.id)

    group = db.query(Group).filter(*filters).first()
    if not group:
        raise HTTPException(status_code=404, detail="Grup tidak ditemukan")
    return group


def _item_to_dict(item: Itinerary) -> dict:
    return {
        "id": item.id,
        "group_id": item.group_id,
        "date": item.date,
        "time_start": item.time_start or "",
        "time_end": item.time_end or "",
        "activity": item.activity,
        "location": item.location or "",
        "notes": item.notes or "",
        "category": item.category or "activity",
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/{group_id}")
async def list_itinerary(
    group_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all itinerary items for a group, sorted by date + time."""
    _get_accessible_group(db, user, group_id)
    items = (
        db.query(Itinerary)
        .filter(Itinerary.group_id == group_id)
        .order_by(Itinerary.date, Itinerary.time_start)
        .all()
    )
    return {"items": [_item_to_dict(i) for i in items]}


@router.post("/{group_id}", status_code=201)
async def create_itinerary(
    group_id: int,
    body: ItineraryCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add an itinerary item to a group."""
    _get_accessible_group(db, user, group_id)

    if not body.activity.strip():
        raise HTTPException(status_code=400, detail="Aktivitas tidak boleh kosong")
    if not body.date.strip():
        raise HTTPException(status_code=400, detail="Tanggal harus diisi")

    item = Itinerary(
        group_id=group_id,
        date=body.date.strip(),
        time_start=body.time_start.strip(),
        time_end=body.time_end.strip(),
        activity=body.activity.strip(),
        location=body.location.strip(),
        notes=body.notes.strip(),
        category=body.category.strip() or "activity",
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    logger.info(f"Added itinerary item '{item.activity}' to group {group_id}")
    return _item_to_dict(item)


@router.put("/{group_id}/{item_id}")
async def update_itinerary(
    group_id: int,
    item_id: int,
    body: ItineraryUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update an itinerary item."""
    _get_accessible_group(db, user, group_id)

    item = db.query(Itinerary).filter(
        Itinerary.id == item_id, Itinerary.group_id == group_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item jadwal tidak ditemukan")

    for field in ["date", "time_start", "time_end", "activity", "location", "notes", "category"]:
        value = getattr(body, field, None)
        if value is not None:
            setattr(item, field, value.strip() if isinstance(value, str) else value)

    db.commit()
    db.refresh(item)
    return _item_to_dict(item)


@router.delete("/{group_id}/{item_id}")
async def delete_itinerary(
    group_id: int,
    item_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete an itinerary item."""
    _get_accessible_group(db, user, group_id)

    item = db.query(Itinerary).filter(
        Itinerary.id == item_id, Itinerary.group_id == group_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item jadwal tidak ditemukan")

    db.delete(item)
    db.commit()
    return {"status": "deleted", "id": item_id}

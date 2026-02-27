"""
Inventory Router — Logistics Checklist API.

Pro-only endpoints for inventory forecasting and fulfillment tracking.
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
from app.services import inventory_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/inventory", tags=["Inventory (Pro)"])


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

class InventoryItemCreate(BaseModel):
    item_name: str
    item_type: str = "other"
    size: str = ""
    total_stock: int = 0

class InventoryItemUpdate(BaseModel):
    total_stock: Optional[int] = None
    distributed_count: Optional[int] = None

class MarkReceivedRequest(BaseModel):
    member_ids: List[int]
    items_received: List[str] = ["koper", "baju"]  # Default items

class UpdateMemberSizeRequest(BaseModel):
    baju_size: str  # S/M/L/XL/XXL
    family_id: str = ""


# =============================================================================
# INVENTORY MASTER ENDPOINTS
# =============================================================================

@router.get("/")
async def list_inventory(
    user: User = Depends(require_pro_plan),
    db: Session = Depends(get_db),
):
    """List all inventory items for the current user."""
    items = inventory_service.get_all_inventory(db, user.id)
    return {"items": items, "total": len(items)}


@router.post("/", status_code=201)
async def create_inventory_item(
    body: InventoryItemCreate,
    user: User = Depends(require_pro_plan),
    db: Session = Depends(get_db),
):
    """Create or update an inventory item."""
    item = inventory_service.get_or_create_inventory(
        db, user.id, body.item_name, body.item_type, body.size
    )
    if body.total_stock > 0:
        item = inventory_service.update_inventory_stock(
            db, user.id, body.item_name, body.total_stock, body.item_type, body.size
        )
    return item.to_dict()


@router.put("/{item_id}")
async def update_inventory_item(
    item_id: int,
    body: InventoryItemUpdate,
    user: User = Depends(require_pro_plan),
    db: Session = Depends(get_db),
):
    """Update an inventory item."""
    from app.models.operational import InventoryMaster
    
    item = db.query(InventoryMaster).filter(
        InventoryMaster.id == item_id,
        InventoryMaster.user_id == user.id
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item tidak ditemukan")
    
    if body.total_stock is not None:
        item.total_stock = body.total_stock
    if body.distributed_count is not None:
        item.distributed_count = body.distributed_count
    
    db.commit()
    db.refresh(item)
    return item.to_dict()


@router.delete("/{item_id}")
async def delete_inventory_item(
    item_id: int,
    user: User = Depends(require_pro_plan),
    db: Session = Depends(get_db),
):
    """Delete an inventory item."""
    from app.models.operational import InventoryMaster
    
    item = db.query(InventoryMaster).filter(
        InventoryMaster.id == item_id,
        InventoryMaster.user_id == user.id
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item tidak ditemukan")
    
    db.delete(item)
    db.commit()
    return {"status": "deleted", "id": item_id}


# =============================================================================
# FORECASTING ENDPOINTS
# =============================================================================

@router.get("/forecast/{group_id}")
async def get_forecast(
    group_id: int,
    user: User = Depends(require_pro_plan),
    db: Session = Depends(get_db),
):
    """
    Generate a forecasting report for a group.
    
    Returns item requirements (koper, ihram, mukena, baju) and size breakdown.
    """
    group = _get_user_group(db, user, group_id)
    report = inventory_service.generate_forecast_report(db, group_id)
    
    return {
        "group_id": group_id,
        "group_name": group.name,
        **report
    }


# =============================================================================
# FULFILLMENT ENDPOINTS
# =============================================================================

@router.get("/fulfillment/{group_id}")
async def get_fulfillment_status(
    group_id: int,
    user: User = Depends(require_pro_plan),
    db: Session = Depends(get_db),
):
    """Get fulfillment status for all members in a group."""
    _get_user_group(db, user, group_id)
    status = inventory_service.get_fulfillment_status(db, group_id)
    return status


@router.post("/fulfillment/{group_id}/mark-received")
async def mark_members_received(
    group_id: int,
    body: MarkReceivedRequest,
    user: User = Depends(require_pro_plan),
    db: Session = Depends(get_db),
):
    """Mark multiple members as having received their equipment."""
    _get_user_group(db, user, group_id)
    result = inventory_service.bulk_mark_received(
        db, group_id, user.id, body.member_ids
    )
    return result


@router.put("/members/{member_id}/operational")
async def update_member_operational(
    member_id: int,
    body: UpdateMemberSizeRequest,
    user: User = Depends(require_pro_plan),
    db: Session = Depends(get_db),
):
    """Update member's baju_size and family_id (operational fields)."""
    member = db.query(GroupMember).filter(GroupMember.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member tidak ditemukan")
    
    # Verify ownership through group
    group = db.query(Group).filter(
        Group.id == member.group_id,
        Group.user_id == user.id
    ).first()
    if not group:
        raise HTTPException(status_code=404, detail="Member tidak ditemukan")
    
    # Update operational fields
    valid_sizes = ["S", "M", "L", "XL", "XXL", ""]
    if body.baju_size.upper() not in valid_sizes:
        raise HTTPException(
            status_code=400,
            detail=f"Ukuran baju tidak valid. Pilih: {', '.join(valid_sizes[:-1])}"
        )
    
    member.baju_size = body.baju_size.upper()
    member.family_id = body.family_id.strip() if body.family_id else ""
    
    db.commit()
    db.refresh(member)
    
    return member.to_dict_full()

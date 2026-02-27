"""
Inventory Service — Logistics Checklist for Jamaah.

Pro-only feature for tracking physical item distribution (suitcases, ihram, mukena).
"""
import logging
from typing import List, Dict, Any, Optional
from collections import Counter
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.group import Group, GroupMember
from app.models.operational import InventoryMaster, ItemType
from app.models.user import User

logger = logging.getLogger(__name__)


# =============================================================================
# INVENTORY MASTER OPERATIONS
# =============================================================================

def get_or_create_inventory(
    db: Session, 
    user_id: int, 
    item_name: str,
    item_type: str = "other",
    size: str = ""
) -> InventoryMaster:
    """Get existing inventory item or create new one."""
    item = db.query(InventoryMaster).filter(
        InventoryMaster.user_id == user_id,
        InventoryMaster.item_name.ilike(item_name.strip()),
        InventoryMaster.size == size
    ).first()
    
    if not item:
        item = InventoryMaster(
            user_id=user_id,
            item_name=item_name.strip(),
            item_type=item_type,
            size=size,
            total_stock=0,
            distributed_count=0
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        logger.info(f"Created inventory item: {item_name} (size={size}) for user {user_id}")
    
    return item


def update_inventory_stock(
    db: Session,
    user_id: int,
    item_name: str,
    quantity: int,
    item_type: str = "other",
    size: str = ""
) -> InventoryMaster:
    """Update total stock for an inventory item."""
    item = get_or_create_inventory(db, user_id, item_name, item_type, size)
    item.total_stock += quantity
    db.commit()
    db.refresh(item)
    logger.info(f"Updated {item_name} stock to {item.total_stock}")
    return item


def get_all_inventory(db: Session, user_id: int) -> List[Dict]:
    """Get all inventory items for a user."""
    items = db.query(InventoryMaster).filter(
        InventoryMaster.user_id == user_id
    ).order_by(InventoryMaster.item_name).all()
    return [item.to_dict() for item in items]


# =============================================================================
# FORECASTING REPORT
# =============================================================================

def generate_forecast_report(db: Session, group_id: int) -> Dict[str, Any]:
    """
    Generate a forecasting report for a specific group.
    
    Logic:
    - Count male pilgrims (title == 'Mr') as needing "Kain Ihram"
    - Count female pilgrims (title in ['Mrs', 'Ms']) as needing "Mukena"
    - Everyone needs a "Koper"
    - Count required baju_size totals
    
    Returns:
        Dict with item requirements and size breakdown
    """
    # Get all members in the group
    members = db.query(GroupMember).filter(GroupMember.group_id == group_id).all()
    
    if not members:
        return {
            "group_id": group_id,
            "total_members": 0,
            "requirements": {},
            "size_breakdown": {},
            "details": []
        }
    
    # Initialize counters
    requirements = {
        "koper": 0,          # Everyone needs a suitcase
        "ihram": 0,          # Males need ihram
        "mukena": 0,         # Females need mukena
        "baju": 0,           # Everyone needs a shirt
    }
    
    size_breakdown = {
        "S": 0, "M": 0, "L": 0, "XL": 0, "XXL": 0, "unknown": 0
    }
    
    details = []
    
    for member in members:
        gender = member.gender
        size = (member.baju_size or "").upper()
        
        # Count items
        requirements["koper"] += 1
        requirements["baju"] += 1
        
        if gender == "male":
            requirements["ihram"] += 1
        elif gender == "female":
            requirements["mukena"] += 1
        
        # Count sizes
        if size in size_breakdown:
            size_breakdown[size] += 1
        else:
            size_breakdown["unknown"] += 1
        
        details.append({
            "member_id": member.id,
            "nama": member.nama,
            "title": member.title,
            "gender": gender,
            "baju_size": member.baju_size or "",
            "needs_ihram": gender == "male",
            "needs_mukena": gender == "female",
            "is_equipment_received": member.is_equipment_received
        })
    
    return {
        "group_id": group_id,
        "total_members": len(members),
        "requirements": requirements,
        "size_breakdown": size_breakdown,
        "details": details
    }


# =============================================================================
# FULFILLMENT OPERATIONS
# =============================================================================

def mark_equipment_received(
    db: Session,
    member_id: int,
    user_id: int,
    items_received: List[str] = None
) -> GroupMember:
    """
    Mark a member as having received their equipment.
    
    Args:
        db: Database session
        member_id: The member to update
        user_id: The user (travel agency) for inventory tracking
        items_received: List of items received (e.g., ["koper", "ihram"])
    
    Returns:
        Updated GroupMember
    """
    member = db.query(GroupMember).filter(GroupMember.id == member_id).first()
    if not member:
        raise ValueError(f"Member {member_id} not found")
    
    # Mark as received
    member.is_equipment_received = True
    
    # Decrement inventory if items specified
    if items_received:
        for item_name in items_received:
            item_name_lower = item_name.lower()
            
            # Map item names to types
            item_type_map = {
                "koper": ItemType.KOPER,
                "ihram": ItemType.IHRAM,
                "mukena": ItemType.MUKENA,
                "baju": ItemType.BAJU,
            }
            
            item_type = item_type_map.get(item_name_lower, ItemType.OTHER)
            
            # Get inventory item (for baju, include size)
            size = member.baju_size if item_name_lower == "baju" else ""
            inventory = get_or_create_inventory(
                db, user_id, item_name_lower.capitalize(), item_type, size
            )
            
            # Decrement distributed count
            if inventory.distributed_count < inventory.total_stock:
                inventory.distributed_count += 1
                logger.info(f"Marked {item_name} as distributed for member {member_id}")
    
    db.commit()
    db.refresh(member)
    return member


def bulk_mark_received(
    db: Session,
    group_id: int,
    user_id: int,
    member_ids: List[int]
) -> Dict[str, Any]:
    """
    Mark multiple members as having received their equipment.
    
    Returns:
        Summary of operation
    """
    updated = []
    errors = []
    
    for member_id in member_ids:
        try:
            member = mark_equipment_received(db, member_id, user_id)
            updated.append(member_id)
        except Exception as e:
            errors.append({"member_id": member_id, "error": str(e)})
    
    return {
        "group_id": group_id,
        "updated_count": len(updated),
        "updated_ids": updated,
        "errors": errors
    }


def get_fulfillment_status(db: Session, group_id: int) -> Dict[str, Any]:
    """
    Get fulfillment status for all members in a group.
    
    Returns:
        Dict with received/pending counts and member lists
    """
    members = db.query(GroupMember).filter(GroupMember.group_id == group_id).all()
    
    received = [m for m in members if m.is_equipment_received]
    pending = [m for m in members if not m.is_equipment_received]
    
    return {
        "group_id": group_id,
        "total_members": len(members),
        "received_count": len(received),
        "pending_count": len(pending),
        "received": [m.to_dict() for m in received],
        "pending": [m.to_dict() for m in pending]
    }

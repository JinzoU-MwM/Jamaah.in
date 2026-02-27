"""
Rooming Service — Auto-Rooming Algorithm for Hotel Allocation.

Pro-only feature for automatically assigning pilgrims to hotel rooms
based on gender and family relationships.
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.models.group import Group, GroupMember
from app.models.operational import Room, RoomType, GenderType
from app.models.user import User

logger = logging.getLogger(__name__)


# =============================================================================
# ROOM OPERATIONS
# =============================================================================

def create_room(
    db: Session,
    group_id: int,
    room_number: str,
    room_type: str = RoomType.QUAD,
    gender_type: str = GenderType.MALE,
    capacity: int = None
) -> Room:
    """Create a new room for a group."""
    # Set capacity based on room type if not specified
    if capacity is None:
        capacity_map = {
            RoomType.QUAD: 4,
            RoomType.TRIPLE: 3,
            RoomType.DOUBLE: 2
        }
        capacity = capacity_map.get(room_type, 4)
    
    room = Room(
        group_id=group_id,
        room_number=room_number.strip(),
        room_type=room_type,
        gender_type=gender_type,
        capacity=capacity,
        is_auto_assigned=False
    )
    db.add(room)
    db.commit()
    db.refresh(room)
    logger.info(f"Created room {room_number} for group {group_id}")
    return room


def get_group_rooms(db: Session, group_id: int) -> List[Dict]:
    """Get all rooms for a group with their members (eager loaded)."""
    rooms = (
        db.query(Room)
        .options(joinedload(Room.members))
        .filter(Room.group_id == group_id)
        .all()
    )
    return [room.to_dict() for room in rooms]


def delete_room(db: Session, room_id: int) -> bool:
    """Delete a room (unassigns all members)."""
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        return False
    
    # Unassign all members in this room
    db.query(GroupMember).filter(GroupMember.room_id == room_id).update(
        {"room_id": None}
    )
    
    db.delete(room)
    db.commit()
    logger.info(f"Deleted room {room_id}")
    return True


def assign_member_to_room(
    db: Session,
    member_id: int,
    room_id: int
) -> GroupMember:
    """Manually assign a member to a room."""
    member = db.query(GroupMember).filter(GroupMember.id == member_id).first()
    if not member:
        raise ValueError(f"Member {member_id} not found")
    
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise ValueError(f"Room {room_id} not found")
    
    if room.is_full:
        raise ValueError(f"Room {room.room_number} is at capacity")
    
    member.room_id = room_id
    db.commit()
    db.refresh(member)
    logger.info(f"Assigned member {member_id} to room {room_id}")
    return member


def unassign_member_from_room(db: Session, member_id: int) -> GroupMember:
    """Remove a member from their room. Auto-deletes the room if it becomes empty."""
    member = db.query(GroupMember).filter(GroupMember.id == member_id).first()
    if not member:
        raise ValueError(f"Member {member_id} not found")
    
    old_room_id = member.room_id
    member.room_id = None
    db.flush()

    # Auto-delete room if it's now empty
    if old_room_id:
        remaining = db.query(func.count(GroupMember.id)).filter(
            GroupMember.room_id == old_room_id
        ).scalar() or 0
        if remaining == 0:
            room = db.query(Room).filter(Room.id == old_room_id).first()
            if room:
                db.delete(room)
                logger.info(f"Auto-deleted empty room {room.room_number} (id={old_room_id})")

    db.commit()
    db.refresh(member)
    return member


# =============================================================================
# AUTO-ROOMING ALGORITHM
# =============================================================================

def generate_auto_rooming(
    db: Session,
    group_id: int,
    room_capacity: int = 4
) -> Dict[str, Any]:
    """
    Automatically assign pilgrims to hotel rooms.
    
    Algorithm:
    1. Group members by family_id
    2. Assign families to rooms first (same family = same room)
    3. Assign remaining males to male-only rooms
    4. Assign remaining females to female-only rooms
    5. No mixing unless they share a family_id
    
    Args:
        db: Database session
        group_id: The group to process
        room_capacity: Maximum people per room (default: 4)
    
    Returns:
        Dict with room assignments and summary
    """
    # Get all unassigned members in the group
    members = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.room_id == None  # Unassigned only
    ).all()
    
    if not members:
        return {
            "group_id": group_id,
            "rooms_created": 0,
            "members_assigned": 0,
            "assignments": {},
            "summary": "No unassigned members to process"
        }
    
    # Step 1: Group by family
    family_groups = defaultdict(list)
    single_males = []
    single_females = []
    
    for member in members:
        if member.family_id and member.family_id.strip():
            family_groups[member.family_id.strip()].append(member)
        else:
            if member.gender == "male":
                single_males.append(member)
            elif member.gender == "female":
                single_females.append(member)
            else:
                # Unknown gender - default to creating separate room
                single_males.append(member)
    
    # Track assignments
    assignments = {}
    rooms_created = 0
    members_assigned = 0
    room_counter = 1
    
    # Step 2: Assign families to rooms
    for family_id, family_members in family_groups.items():
        # Determine family gender type
        genders = set(m.gender for m in family_members)
        if len(genders) > 1:
            family_gender_type = GenderType.FAMILY
        elif "male" in genders:
            family_gender_type = GenderType.MALE
        else:
            family_gender_type = GenderType.FEMALE
        
        # Split into multiple rooms if family exceeds capacity
        for i in range(0, len(family_members), room_capacity):
            batch = family_members[i:i + room_capacity]
            
            # Create room
            room_number = f"F{family_id[-3:]}-{room_counter}"
            room = Room(
                group_id=group_id,
                room_number=room_number,
                room_type=RoomType.QUAD,
                gender_type=family_gender_type,
                capacity=room_capacity,
                is_auto_assigned=True
            )
            db.add(room)
            db.flush()  # Get room.id
            
            # Assign members
            for member in batch:
                member.room_id = room.id
                members_assigned += 1
            
            assignments[room_number] = {
                "room_id": room.id,
                "room_number": room_number,
                "gender_type": family_gender_type,
                "is_family": True,
                "family_id": family_id,
                "member_ids": [m.id for m in batch],
                "member_names": [m.nama for m in batch]
            }
            
            rooms_created += 1
            room_counter += 1
    
    # Step 3: Assign single males
    for i in range(0, len(single_males), room_capacity):
        batch = single_males[i:i + room_capacity]
        
        room_number = f"M-{room_counter:03d}"
        room = Room(
            group_id=group_id,
            room_number=room_number,
            room_type=RoomType.QUAD,
            gender_type=GenderType.MALE,
            capacity=room_capacity,
            is_auto_assigned=True
        )
        db.add(room)
        db.flush()
        
        for member in batch:
            member.room_id = room.id
            members_assigned += 1
        
        assignments[room_number] = {
            "room_id": room.id,
            "room_number": room_number,
            "gender_type": GenderType.MALE,
            "is_family": False,
            "family_id": None,
            "member_ids": [m.id for m in batch],
            "member_names": [m.nama for m in batch]
        }
        
        rooms_created += 1
        room_counter += 1
    
    # Step 4: Assign single females
    for i in range(0, len(single_females), room_capacity):
        batch = single_females[i:i + room_capacity]
        
        room_number = f"F-{room_counter:03d}"
        room = Room(
            group_id=group_id,
            room_number=room_number,
            room_type=RoomType.QUAD,
            gender_type=GenderType.FEMALE,
            capacity=room_capacity,
            is_auto_assigned=True
        )
        db.add(room)
        db.flush()
        
        for member in batch:
            member.room_id = room.id
            members_assigned += 1
        
        assignments[room_number] = {
            "room_id": room.id,
            "room_number": room_number,
            "gender_type": GenderType.FEMALE,
            "is_family": False,
            "family_id": None,
            "member_ids": [m.id for m in batch],
            "member_names": [m.nama for m in batch]
        }
        
        rooms_created += 1
        room_counter += 1
    
    db.commit()
    
    logger.info(f"Auto-rooming complete for group {group_id}: {rooms_created} rooms, {members_assigned} members")
    
    return {
        "group_id": group_id,
        "rooms_created": rooms_created,
        "members_assigned": members_assigned,
        "assignments": assignments,
        "summary": f"Created {rooms_created} rooms for {members_assigned} members"
    }


def clear_room_assignments(db: Session, group_id: int) -> int:
    """Clear all room assignments for a group (for re-running auto-rooming)."""
    # Unassign all members first
    updated = db.query(GroupMember).filter(
        GroupMember.group_id == group_id
    ).update({"room_id": None}, synchronize_session=False)
    
    db.flush()  # Ensure FK nulls are written before deleting rooms
    
    # Delete ALL rooms for this group
    deleted = db.query(Room).filter(
        Room.group_id == group_id
    ).delete(synchronize_session=False)
    
    db.commit()
    logger.info(f"Cleared room assignments for group {group_id}: {updated} members, {deleted} rooms")
    return updated


# =============================================================================
# ROOMING SUMMARY
# =============================================================================

def get_rooming_summary(db: Session, group_id: int) -> Dict[str, Any]:
    """Get a summary of room assignments for a group using SQL aggregates."""
    # Use SQL COUNT instead of loading all member objects
    total_members = db.query(func.count(GroupMember.id)).filter(
        GroupMember.group_id == group_id
    ).scalar() or 0

    assigned_count = db.query(func.count(GroupMember.id)).filter(
        GroupMember.group_id == group_id,
        GroupMember.room_id != None
    ).scalar() or 0

    unassigned_count = total_members - assigned_count

    # Room details with occupancy (eager load members for count)
    rooms = (
        db.query(Room)
        .options(joinedload(Room.members))
        .filter(Room.group_id == group_id)
        .all()
    )

    room_details = []
    for room in rooms:
        room_details.append({
            "id": room.id,
            "room_number": room.room_number,
            "gender_type": room.gender_type,
            "capacity": room.capacity,
            "occupied": room.occupied_count,
            "available": room.available_slots,
            "is_full": room.is_full,
            "is_auto_assigned": room.is_auto_assigned
        })

    return {
        "group_id": group_id,
        "total_members": total_members,
        "assigned_count": assigned_count,
        "unassigned_count": unassigned_count,
        "total_rooms": len(rooms),
        "rooms": room_details
    }

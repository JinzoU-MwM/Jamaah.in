"""
Operational models: InventoryMaster and Room for Pro features.
These are internal-use models NOT exported to Siskopatuh Excel.
"""
import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SAEnum, Boolean
from sqlalchemy.orm import relationship
from app.database import Base


class RoomType(str, enum.Enum):
    """Hotel room types by occupancy."""
    QUAD = "quad"      # 4 people
    TRIPLE = "triple"  # 3 people
    DOUBLE = "double"  # 2 people


class GenderType(str, enum.Enum):
    """Room gender assignment rules."""
    MALE = "male"
    FEMALE = "female"
    FAMILY = "family"  # Mixed family members


class ItemType(str, enum.Enum):
    """Types of inventory items."""
    KOPER = "koper"        # Suitcase
    IHRAM = "ihram"        # Male prayer garment
    MUKENA = "mukena"      # Female prayer garment
    BAJU = "baju"          # Shirt/uniform
    TAS = "tas"            # Bag
    OTHER = "other"        # Other items


class InventoryMaster(Base):
    """
    Master inventory for a user/travel agency.
    Tracks total stock of physical items to be distributed to pilgrims.
    """
    __tablename__ = "inventory_master"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Item details
    item_name = Column(String(255), nullable=False)  # e.g., "Koper", "Kain Ihram", "Mukena"
    item_type = Column(String(50), default=ItemType.OTHER)
    size = Column(String(20), default="")  # S/M/L/XL/XXL for baju
    
    # Stock tracking
    total_stock = Column(Integer, default=0)
    distributed_count = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", backref="inventory_items")
    
    @property
    def remaining_stock(self):
        """Calculate remaining stock."""
        return self.total_stock - self.distributed_count
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "item_name": self.item_name,
            "item_type": self.item_type,
            "size": self.size,
            "total_stock": self.total_stock,
            "distributed_count": self.distributed_count,
            "remaining_stock": self.remaining_stock,
        }


class Room(Base):
    """
    Hotel room for a specific group/trip.
    Rooms are assigned based on gender and family relationships.
    """
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Room details
    room_number = Column(String(50), nullable=False)  # e.g., "301", "A-101"
    room_type = Column(String(20), default=RoomType.QUAD)
    gender_type = Column(String(20), default=GenderType.MALE)
    capacity = Column(Integer, default=4)
    
    # Assignment metadata
    is_auto_assigned = Column(Boolean, default=False)  # True if auto-rooming was used
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    group = relationship("Group", backref="rooms")
    members = relationship("GroupMember", back_populates="room")
    
    @property
    def occupied_count(self):
        """Count members currently assigned to this room."""
        return len(self.members)
    
    @property
    def is_full(self):
        """Check if room is at capacity."""
        return self.occupied_count >= self.capacity
    
    @property
    def available_slots(self):
        """Count available slots."""
        return self.capacity - self.occupied_count
    
    def to_dict(self):
        return {
            "id": self.id,
            "group_id": self.group_id,
            "room_number": self.room_number,
            "room_type": self.room_type,
            "gender_type": self.gender_type,
            "capacity": self.capacity,
            "occupied": self.occupied_count,
            "available_slots": self.available_slots,
            "is_full": self.is_full,
            "is_auto_assigned": self.is_auto_assigned,
            "member_ids": [m.id for m in self.members],
            "members": [
                {"id": m.id, "nama": m.nama or "", "title": m.title or "", "no_paspor": m.no_paspor or ""}
                for m in self.members
            ],
        }

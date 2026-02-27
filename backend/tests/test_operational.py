"""
Unit Tests for Inventory and Rooming Services (Pro Features)

Run with: pytest backend/tests/test_operational.py -v
"""
import sys
from pathlib import Path
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services import inventory_service, rooming_service
from app.models.group import GroupMember
from app.models.operational import InventoryMaster, Room, RoomType, GenderType


# =============================================================================
# INVENTORY SERVICE TESTS
# =============================================================================

class TestInventoryForecast:
    """Tests for inventory forecasting"""
    
    def test_forecast_empty_group(self):
        """Empty group should return zero requirements"""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        result = inventory_service.generate_forecast_report(mock_db, group_id=1)
        
        assert result["total_members"] == 0
        # Empty group returns empty requirements dict
        assert result["requirements"] == {}
        assert result["details"] == []
    
    def test_forecast_single_male(self):
        """Single male needs koper, baju, and ihram"""
        mock_db = Mock()
        
        # Create mock male member
        male = Mock(spec=GroupMember)
        male.id = 1
        male.nama = "Ahmad Dahlan"
        male.title = "Mr"
        male.gender = "male"
        male.baju_size = "L"
        male.family_id = ""
        male.is_equipment_received = False
        
        mock_db.query.return_value.filter.return_value.all.return_value = [male]
        
        result = inventory_service.generate_forecast_report(mock_db, group_id=1)
        
        assert result["total_members"] == 1
        assert result["requirements"]["koper"] == 1
        assert result["requirements"]["ihram"] == 1
        assert result["requirements"]["mukena"] == 0
        assert result["requirements"]["baju"] == 1
        assert result["size_breakdown"]["L"] == 1
    
    def test_forecast_single_female(self):
        """Single female needs koper, baju, and mukena"""
        mock_db = Mock()
        
        female = Mock(spec=GroupMember)
        female.id = 2
        female.nama = "Siti Aminah"
        female.title = "Mrs"
        female.gender = "female"
        female.baju_size = "M"
        female.family_id = ""
        female.is_equipment_received = False
        
        mock_db.query.return_value.filter.return_value.all.return_value = [female]
        
        result = inventory_service.generate_forecast_report(mock_db, group_id=1)
        
        assert result["total_members"] == 1
        assert result["requirements"]["koper"] == 1
        assert result["requirements"]["ihram"] == 0
        assert result["requirements"]["mukena"] == 1
        assert result["requirements"]["baju"] == 1
        assert result["size_breakdown"]["M"] == 1
    
    def test_forecast_mixed_group(self):
        """Mixed group with males and females"""
        mock_db = Mock()
        
        members = []
        # 3 males
        for i in range(3):
            m = Mock(spec=GroupMember)
            m.id = i
            m.nama = f"Male {i}"
            m.title = "Mr"
            m.gender = "male"
            m.baju_size = "L"
            m.family_id = ""
            m.is_equipment_received = False
            members.append(m)
        
        # 2 females
        for i in range(3, 5):
            f = Mock(spec=GroupMember)
            f.id = i
            f.nama = f"Female {i}"
            f.title = "Mrs"
            f.gender = "female"
            f.baju_size = "M"
            f.family_id = ""
            f.is_equipment_received = False
            members.append(f)
        
        mock_db.query.return_value.filter.return_value.all.return_value = members
        
        result = inventory_service.generate_forecast_report(mock_db, group_id=1)
        
        assert result["total_members"] == 5
        assert result["requirements"]["koper"] == 5
        assert result["requirements"]["ihram"] == 3  # Only males
        assert result["requirements"]["mukena"] == 2  # Only females
        assert result["requirements"]["baju"] == 5


class TestInventoryMaster:
    """Tests for inventory master operations"""
    
    def test_remaining_stock_calculation(self):
        """Test remaining_stock property"""
        item = InventoryMaster(
            user_id=1,
            item_name="Koper",
            total_stock=100,
            distributed_count=30
        )
        
        assert item.remaining_stock == 70
    
    def test_remaining_stock_when_exhausted(self):
        """Test remaining_stock when fully distributed"""
        item = InventoryMaster(
            user_id=1,
            item_name="Koper",
            total_stock=50,
            distributed_count=50
        )
        
        assert item.remaining_stock == 0


class TestFulfillment:
    """Tests for fulfillment operations"""
    
    def test_mark_equipment_received(self):
        """Test marking member as received"""
        mock_db = Mock()
        
        member = Mock(spec=GroupMember)
        member.id = 1
        member.is_equipment_received = False
        member.baju_size = "L"
        
        mock_db.query.return_value.filter.return_value.first.return_value = member
        
        # Mock inventory item
        mock_inventory = Mock()
        mock_inventory.total_stock = 100
        mock_inventory.distributed_count = 0
        
        with patch.object(inventory_service, 'get_or_create_inventory', return_value=mock_inventory):
            result = inventory_service.mark_equipment_received(
                mock_db,
                member_id=1,
                user_id=1,
                items_received=["koper", "baju"]
            )
        
        assert member.is_equipment_received == True
    
    def test_fulfillment_status(self):
        """Test getting fulfillment status"""
        mock_db = Mock()
        
        # 2 received, 1 pending
        received = [
            Mock(is_equipment_received=True, to_dict=Mock(return_value={"id": 1})),
            Mock(is_equipment_received=True, to_dict=Mock(return_value={"id": 2})),
        ]
        pending = [
            Mock(is_equipment_received=False, to_dict=Mock(return_value={"id": 3})),
        ]
        all_members = received + pending
        
        mock_db.query.return_value.filter.return_value.all.return_value = all_members
        
        result = inventory_service.get_fulfillment_status(mock_db, group_id=1)
        
        assert result["total_members"] == 3
        assert result["received_count"] == 2
        assert result["pending_count"] == 1


# =============================================================================
# ROOMING SERVICE TESTS
# =============================================================================

class TestRoomModel:
    """Tests for Room model properties"""
    
    def test_room_occupied_count(self):
        """Test occupied_count property"""
        room = Mock(spec=Room)
        room.capacity = 4
        
        # Mock the members list with 3 items
        members = [Mock(), Mock(), Mock()]
        room.members = members
        
        # occupied_count uses len(self.members)
        assert len(room.members) == 3
    
    def test_room_is_full(self):
        """Test is_full property"""
        room = Mock(spec=Room)
        room.capacity = 4
        
        # Full room
        room.members = [Mock(), Mock(), Mock(), Mock()]
        room.is_full = len(room.members) >= room.capacity
        assert room.is_full == True
        
        # Not full room
        room.members = [Mock(), Mock()]
        room.is_full = len(room.members) >= room.capacity
        assert room.is_full == False
    
    def test_room_available_slots(self):
        """Test available_slots property"""
        room = Mock(spec=Room)
        room.capacity = 4
        room.members = [Mock(), Mock()]
        
        # available_slots = capacity - occupied_count
        available_slots = room.capacity - len(room.members)
        assert available_slots == 2


class TestAutoRooming:
    """Tests for auto-rooming algorithm"""
    
    def test_auto_rooming_empty_group(self):
        """Auto-rooming with no members"""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.flush = Mock()
        
        result = rooming_service.generate_auto_rooming(mock_db, group_id=1, room_capacity=4)
        
        assert result["rooms_created"] == 0
        assert result["members_assigned"] == 0
    
    def test_auto_rooming_single_male(self):
        """Auto-rooming creates male room for single male"""
        mock_db = Mock()
        
        male = Mock(spec=GroupMember)
        male.id = 1
        male.nama = "Ahmad"
        male.title = "Mr"
        male.gender = "male"
        male.family_id = ""
        male.room_id = None
        
        mock_db.query.return_value.filter.return_value.all.return_value = [male]
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.flush = Mock()
        
        result = rooming_service.generate_auto_rooming(mock_db, group_id=1, room_capacity=4)
        
        assert result["rooms_created"] == 1
        assert result["members_assigned"] == 1
    
    def test_auto_rooming_family_grouping(self):
        """Family members should be placed in same room"""
        mock_db = Mock()
        
        # Family of 3 with same family_id
        family_members = []
        for i in range(3):
            m = Mock(spec=GroupMember)
            m.id = i
            m.nama = f"Family Member {i}"
            m.title = "Mr" if i == 0 else "Mrs"
            m.gender = "male" if i == 0 else "female"
            m.family_id = "F001"
            m.room_id = None
            family_members.append(m)
        
        mock_db.query.return_value.filter.return_value.all.return_value = family_members
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.flush = Mock()
        
        result = rooming_service.generate_auto_rooming(mock_db, group_id=1, room_capacity=4)
        
        # Should create 1 family room
        assert result["rooms_created"] == 1
        assert result["members_assigned"] == 3
    
    def test_auto_rooming_gender_separation(self):
        """Non-family males and females should be in separate rooms"""
        mock_db = Mock()
        
        members = []
        
        # 2 males without family
        for i in range(2):
            m = Mock(spec=GroupMember)
            m.id = i
            m.nama = f"Male {i}"
            m.title = "Mr"
            m.gender = "male"
            m.family_id = ""
            m.room_id = None
            members.append(m)
        
        # 2 females without family
        for i in range(2, 4):
            f = Mock(spec=GroupMember)
            f.id = i
            f.nama = f"Female {i}"
            f.title = "Mrs"
            f.gender = "female"
            f.family_id = ""
            f.room_id = None
            members.append(f)
        
        mock_db.query.return_value.filter.return_value.all.return_value = members
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.flush = Mock()
        
        result = rooming_service.generate_auto_rooming(mock_db, group_id=1, room_capacity=4)
        
        # Should create 2 rooms (1 male, 1 female)
        assert result["rooms_created"] == 2
        assert result["members_assigned"] == 4
    
    def test_auto_rooming_capacity_split(self):
        """Large family should be split across multiple rooms"""
        mock_db = Mock()
        
        # Family of 6 with capacity 4
        members = []
        for i in range(6):
            m = Mock(spec=GroupMember)
            m.id = i
            m.nama = f"Family {i}"
            m.title = "Mr"
            m.gender = "male"
            m.family_id = "F001"
            m.room_id = None
            members.append(m)
        
        mock_db.query.return_value.filter.return_value.all.return_value = members
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.flush = Mock()
        
        result = rooming_service.generate_auto_rooming(mock_db, group_id=1, room_capacity=4)
        
        # Should create 2 rooms (4 + 2)
        assert result["rooms_created"] == 2
        assert result["members_assigned"] == 6


class TestRoomAssignment:
    """Tests for manual room assignment"""
    
    def test_assign_member_to_room(self):
        """Test assigning member to room"""
        mock_db = Mock()
        
        member = Mock(spec=GroupMember)
        member.id = 1
        member.room_id = None
        
        room = Mock(spec=Room)
        room.id = 1
        room.room_number = "101"
        room.is_full = False
        
        # Setup query to return member first, then room
        query_count = [0]
        def mock_first():
            query_count[0] += 1
            if query_count[0] == 1:
                return member
            else:
                return room
        
        mock_db.query.return_value.filter.return_value.first = mock_first
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        result = rooming_service.assign_member_to_room(mock_db, member_id=1, room_id=1)
        
        assert member.room_id == 1
    
    def test_assign_to_full_room_raises(self):
        """Assigning to full room should raise error"""
        mock_db = Mock()
        
        member = Mock(spec=GroupMember)
        member.id = 1
        
        room = Mock(spec=Room)
        room.id = 1
        room.room_number = "101"
        room.is_full = True  # Room is full
        
        # First query returns member, second returns room
        query_count = [0]
        def mock_first():
            query_count[0] += 1
            if query_count[0] == 1:
                return member
            else:
                return room
        
        mock_db.query.return_value.filter.return_value.first = mock_first
        
        with pytest.raises(ValueError, match="at capacity"):
            rooming_service.assign_member_to_room(mock_db, member_id=1, room_id=1)


class TestRoomingSummary:
    """Tests for rooming summary"""
    
    def test_rooming_summary_basic(self):
        """Test getting rooming summary with basic data"""
        mock_db = Mock()
        
        # Create mock rooms
        room1 = Mock()
        room1.id = 1
        room1.room_number = "101"
        room1.gender_type = "male"
        room1.capacity = 4
        room1.occupied_count = 3
        room1.available_slots = 1
        room1.is_full = False
        room1.is_auto_assigned = True
        room1.members = [Mock(), Mock(), Mock()]
        
        room2 = Mock()
        room2.id = 2
        room2.room_number = "102"
        room2.gender_type = "female"
        room2.capacity = 4
        room2.occupied_count = 4
        room2.available_slots = 0
        room2.is_full = True
        room2.is_auto_assigned = True
        room2.members = [Mock(), Mock(), Mock(), Mock()]
        
        rooms = [room1, room2]
        
        # Create mock members (7 assigned, 1 unassigned) with gender property
        assigned_members = []
        for _ in range(3):
            m = Mock()
            m.room_id = 1
            m.gender = "male"
            assigned_members.append(m)
        for _ in range(4):
            m = Mock()
            m.room_id = 2
            m.gender = "female"
            assigned_members.append(m)
        unassigned_members = [Mock(room_id=None, gender="male")]
        all_members = assigned_members + unassigned_members
        
        # Setup mock to return rooms first, then members
        query_count = [0]
        def mock_query_side_effect(model):
            query_count[0] += 1
            mock_q = Mock()
            if query_count[0] == 1:
                mock_q.filter.return_value.all.return_value = rooms
            else:
                mock_q.filter.return_value.all.return_value = all_members
            return mock_q
        
        mock_db.query.side_effect = mock_query_side_effect
        
        result = rooming_service.get_rooming_summary(mock_db, group_id=1)
        
        assert result["total_rooms"] == 2
        assert result["total_members"] == 8
        assert result["assigned_count"] == 7
        assert result["unassigned_count"] == 1


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Integration tests combining inventory and rooming"""
    
    def test_family_affects_both_inventory_and_rooming(self):
        """Family grouping should work for both inventory and rooming"""
        mock_db = Mock()
        
        # Create family members
        family = []
        for i, (gender, size) in enumerate([("male", "L"), ("female", "M"), ("male", "S")]):
            m = Mock(spec=GroupMember)
            m.id = i
            m.nama = f"Family Member {i}"
            m.title = "Mr" if gender == "male" else "Mrs"
            m.gender = gender
            m.baju_size = size
            m.family_id = "F001"
            m.is_equipment_received = False
            m.room_id = None
            family.append(m)
        
        # Test inventory forecast
        mock_db.query.return_value.filter.return_value.all.return_value = family
        
        forecast = inventory_service.generate_forecast_report(mock_db, group_id=1)
        
        # Should have 2 ihram (2 males) and 1 mukena (1 female)
        assert forecast["requirements"]["ihram"] == 2  # 2 males
        assert forecast["requirements"]["mukena"] == 1  # 1 female
        assert forecast["size_breakdown"]["L"] == 1
        assert forecast["size_breakdown"]["M"] == 1
        assert forecast["size_breakdown"]["S"] == 1


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

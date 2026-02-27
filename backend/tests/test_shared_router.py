"""
Unit tests for Mutawwif Mobile Manifest feature (shared_router)
Run with: pytest backend/tests/test_shared_router.py -v
"""
import sys
import os
import uuid
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# Add backend directory to python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from main import app
from app.database import get_db
from app.routers.shared_router import require_pro_plan
from app.models.group import Group, GroupMember
from app.models.operational import Room
from app.models.user import User

# Mock User
mock_user = User(id=1, email="test@example.com", is_active=True)

# Override Pro Plan dependency
def override_require_pro_plan():
    return mock_user

app.dependency_overrides[require_pro_plan] = override_require_pro_plan

client = TestClient(app)

class TestSharedRouter:
    def setup_method(self):
        self.mock_db = Mock()
        app.dependency_overrides[get_db] = lambda: self.mock_db

    def teardown_method(self):
        app.dependency_overrides.pop(get_db, None)

    def test_share_group_success(self):
        # Mock group
        group = Group(id=1, user_id=1, name="Umroh Trip VIP", shared_token=None, shared_pin=None, shared_expires_at=None)
        self.mock_db.query.return_value.filter.return_value.first.return_value = group
        
        response = client.post(
            "/groups/1/share",
            json={"pin": "1234", "expires_in_days": 30}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "shared_token" in data
        assert data["pin"] == "1234"
        assert group.shared_pin == "1234"
        assert group.shared_token is not None
        self.mock_db.commit.assert_called_once()
    
    def test_share_group_not_found(self):
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        response = client.post(
            "/groups/999/share",
            json={"pin": "1234", "expires_in_days": 30}
        )
        
        assert response.status_code == 404

    def test_get_shared_manifest_success(self):
        token = uuid.uuid4().hex
        group = Group(id=1, name="Umroh Trip VIP", shared_token=token, shared_pin="1234", shared_expires_at=datetime.utcnow() + timedelta(days=10))
        
        member1 = GroupMember(id=1, group_id=1, nama="Ahmad", title="Mr", no_paspor="A123", no_hp="0812", baju_size="L", room_id=1, is_equipment_received=True)
        member2 = GroupMember(id=2, group_id=1, nama="Siti", title="Mrs", no_paspor="B456", no_hp="0813", baju_size="M", room_id=None, is_equipment_received=False)
        
        room = Room(id=1, room_number="101")
        
        def mock_query(model):
            q = Mock()
            if model == Group:
                q.filter.return_value.first.return_value = group
            elif model == GroupMember:
                q.filter.return_value.order_by.return_value.all.return_value = [member1, member2]
            elif model == Room:
                q.filter.return_value.first.return_value = room
            return q
            
        self.mock_db.query.side_effect = mock_query
        
        response = client.post(
            f"/shared/manifest/{token}",
            json={"pin": "1234"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["group_name"] == "Umroh Trip VIP"
        assert data["total_members"] == 2
        
        assert data["members"][0]["nama"] == "Ahmad"
        assert data["members"][0]["title"] == "Mr"
        assert "is_equipment_received" in data["members"][0]
        assert data["members"][0]["room_number"] == "101"
        assert "nik" not in data["members"][0] # Privacy check
        
        # Second member has no room assigned
        assert data["members"][1]["nama"] == "Siti"
        assert data["members"][1]["room_number"] is None

    def test_get_shared_manifest_invalid_pin(self):
        token = "some-token"
        group = Group(id=1, name="Umroh VIP", shared_token=token, shared_pin="1234", shared_expires_at=datetime.utcnow() + timedelta(days=10))
        
        def mock_query(model):
            q = Mock()
            if model == Group:
                q.filter.return_value.first.return_value = group
            return q
            
        self.mock_db.query.side_effect = mock_query
        
        response = client.post(
            f"/shared/manifest/{token}",
            json={"pin": "wrong"}
        )
        
        assert response.status_code == 401
        assert "PIN salah" in str(response.json())

    def test_get_shared_manifest_expired(self):
        token = "expired-token"
        # Set expiry to past
        group = Group(id=1, name="Umroh VIP", shared_token=token, shared_pin="1234", shared_expires_at=datetime.utcnow() - timedelta(days=1))
        
        def mock_query(model):
            q = Mock()
            if model == Group:
                q.filter.return_value.first.return_value = group
            return q
            
        self.mock_db.query.side_effect = mock_query
        
        response = client.post(
            f"/shared/manifest/{token}",
            json={"pin": "1234"}
        )
        
        assert response.status_code == 401
        assert "kedaluwarsa" in str(response.json())

    def test_revoke_share(self):
        group = Group(id=1, user_id=1, name="Umroh Trip", shared_token="token", shared_pin="1234", shared_expires_at=datetime.utcnow() + timedelta(days=1))
        self.mock_db.query.return_value.filter.return_value.first.return_value = group
        
        response = client.delete("/groups/1/share")
        
        assert response.status_code == 200
        assert group.shared_token is None
        assert group.shared_pin is None
        assert group.shared_expires_at is None
        self.mock_db.commit.assert_called_once()
        
if __name__ == "__main__":
    pytest.main([__file__, "-v"])

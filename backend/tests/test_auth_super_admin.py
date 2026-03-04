import os
import sys
from pathlib import Path

# Add backend directory to path so we can import app
sys.path.append(str(Path(__file__).parent.parent))

from app.auth import is_super_admin_user


class DummyUser:
    def __init__(self, email: str, is_super_admin: bool = False):
        self.email = email
        self.is_super_admin = is_super_admin


def test_super_admin_by_db_flag(monkeypatch):
    monkeypatch.delenv("SUPER_ADMIN_EMAIL", raising=False)
    user = DummyUser("staff@example.com", is_super_admin=True)
    assert is_super_admin_user(user) is True


def test_super_admin_by_env_email(monkeypatch):
    monkeypatch.setenv("SUPER_ADMIN_EMAIL", "owner@example.com")
    user = DummyUser("owner@example.com", is_super_admin=False)
    assert is_super_admin_user(user) is True


def test_not_super_admin(monkeypatch):
    monkeypatch.setenv("SUPER_ADMIN_EMAIL", "owner@example.com")
    user = DummyUser("staff@example.com", is_super_admin=False)
    assert is_super_admin_user(user) is False

"""
Organization / Team models for multi-user access.

Organization → TeamMembers (users with roles)
Groups can optionally belong to an Organization (shared across team).
"""
from datetime import datetime, timedelta
import uuid
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class TeamRole(str, enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    VIEWER = "viewer"


class MemberStatus(str, enum.Enum):
    ACTIVE = "active"
    PENDING = "pending"
    REMOVED = "removed"


class Organization(Base):
    """A travel agency or company that owns shared groups."""
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    team_members = relationship("TeamMember", back_populates="organization", cascade="all, delete-orphan")
    creator = relationship("User", foreign_keys=[created_by])

    @property
    def member_count(self):
        return len([m for m in self.team_members if m.status == MemberStatus.ACTIVE])


class TeamMember(Base):
    """A user's membership in an organization with a specific role."""
    __tablename__ = "team_members"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), default=TeamRole.VIEWER)
    status = Column(String(20), default=MemberStatus.ACTIVE)
    invited_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    joined_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    organization = relationship("Organization", back_populates="team_members")
    user = relationship("User", foreign_keys=[user_id])
    inviter = relationship("User", foreign_keys=[invited_by])


class TeamInvite(Base):
    """Pending invitation to join an organization."""
    __tablename__ = "team_invites"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    role = Column(String(20), default=TeamRole.VIEWER)
    token = Column(String(64), unique=True, index=True, default=lambda: uuid.uuid4().hex)
    invited_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(days=7))
    status = Column(String(20), default="pending")  # pending | accepted | expired

    # Relationships
    organization = relationship("Organization")
    inviter = relationship("User", foreign_keys=[invited_by])

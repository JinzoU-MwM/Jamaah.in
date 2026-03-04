from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base
import secrets


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class RegistrationLink(Base):
    __tablename__ = "registration_links"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(
        Integer, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False
    )
    token = Column(String(64), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=utc_now)
    is_active = Column(Boolean, default=True)

    # Relationships
    group = relationship("Group", back_populates="registration_links")
    creator = relationship("User")

    @staticmethod
    def generate_token():
        return secrets.token_urlsafe(32)

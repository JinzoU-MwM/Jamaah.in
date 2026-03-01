"""
User, Subscription, and UsageLog models
"""
from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class PlanType(str, enum.Enum):
    FREE = "free"
    PRO = "pro"


class SubscriptionStatus(str, enum.Enum):
    TRIAL = "trial"
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    avatar_color = Column(String(30), default="emerald")
    notify_usage_limit = Column(Boolean, default=True)
    notify_expiry = Column(Boolean, default=True)

    # Phone verification (for anti-abuse)
    phone_number = Column(String(20), unique=True, nullable=True, index=True)
    phone_verified = Column(Boolean, default=False)
    phone_otp_code = Column(String(255), nullable=True)  # bcrypt hash
    phone_otp_expires = Column(DateTime, nullable=True)
    trial_used_at = Column(DateTime, nullable=True)  # When Pro Trial was activated

    # Email verification & password reset
    email_verified = Column(Boolean, default=False)
    otp_code = Column(String(255), nullable=True)
    otp_expires = Column(DateTime, nullable=True)
    reset_code = Column(String(255), nullable=True)
    reset_expires = Column(DateTime, nullable=True)

    # Relationships
    subscription = relationship("Subscription", back_populates="user", uselist=False)
    usage_logs = relationship("UsageLog", back_populates="user")

    @property
    def total_usage(self):
        """Total document scans across all time."""
        return sum(log.count for log in self.usage_logs)


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    plan = Column(String(20), default=PlanType.FREE)
    status = Column(String(20), default=SubscriptionStatus.TRIAL)

    # Trial tracking
    trial_start = Column(DateTime, default=datetime.utcnow)
    trial_end = Column(DateTime)

    # Paid subscription tracking
    subscribed_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)

    # Payment reference (manual payment receipt)
    payment_ref = Column(String(255), nullable=True)

    user = relationship("User", back_populates="subscription")

    @property
    def is_trial_active(self):
        """Check if trial period is still active."""
        if self.status != SubscriptionStatus.TRIAL:
            return False
        if not self.trial_end:
            return False
        return datetime.utcnow() < self.trial_end

    @property
    def is_subscription_active(self):
        """Check if paid subscription is active."""
        if self.status != SubscriptionStatus.ACTIVE:
            return False
        if not self.expires_at:
            return False
        return datetime.utcnow() < self.expires_at

    @property
    def has_access(self):
        """Check if user has any form of valid access (trial or paid)."""
        return self.is_trial_active or self.is_subscription_active


class UsageLog(Base):
    __tablename__ = "usage_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(50), default="document_scan")
    count = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="usage_logs")


class PaymentStatus:
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    order_id = Column(String(100), unique=True, index=True, nullable=False)
    amount = Column(Integer, nullable=False)
    status = Column(String(20), default=PaymentStatus.PENDING)
    pakasir_ref = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    paid_at = Column(DateTime, nullable=True)

    user = relationship("User")

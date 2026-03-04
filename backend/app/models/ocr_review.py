"""
OCR processing logs and manual review queue models.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float, Boolean
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class OcrProcessingLog(Base):
    """Per-file OCR processing telemetry used for dashboard metrics."""
    __tablename__ = "ocr_processing_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    session_id = Column(String(64), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    status = Column(String(20), nullable=False, index=True)  # success | partial | failed
    document_type = Column(String(40), default="")
    error_category = Column(String(80), default="", index=True)
    processing_ms = Column(Float, default=0.0)
    cached = Column(Boolean, default=False)
    provenance_json = Column(Text, default="")
    created_at = Column(DateTime, default=utc_now, index=True)

    user = relationship("User")


class OcrReviewItem(Base):
    """Queue item for manual review on problematic OCR outputs."""
    __tablename__ = "ocr_review_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    session_id = Column(String(64), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    status = Column(String(20), default="pending", index=True)  # pending | approved | rejected
    reason = Column(Text, default="")
    document_type = Column(String(40), default="")
    error_category = Column(String(80), default="")
    confidence_score = Column(Float, nullable=True)
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=utc_now, index=True)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    user = relationship("User", foreign_keys=[user_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])

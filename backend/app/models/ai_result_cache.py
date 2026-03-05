"""
Persistent cache model for AI (Gemini) results.
"""
from sqlalchemy import Column, Integer, String, DateTime, Text

from app.database import Base
from app.models.user import utc_now


class AIResultCache(Base):
    __tablename__ = "ai_result_cache"

    id = Column(Integer, primary_key=True, index=True)
    cache_key = Column(String(64), unique=True, nullable=False, index=True)
    input_hash = Column(String(64), nullable=False, index=True)
    model = Column(String(120), nullable=False, index=True)
    prompt_version = Column(String(64), nullable=False, index=True)
    task_type = Column(String(120), nullable=False, index=True)
    result_json = Column(Text, nullable=False)
    hits = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False, index=True)
    last_accessed_at = Column(DateTime, default=utc_now, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)


from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class ExportTemplate(Base):
    """User-uploaded Excel template for custom exports."""
    __tablename__ = "export_templates"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    name = Column(String(100), nullable=False)
    file_path = Column(String(255), nullable=False)
    column_mapping = Column(JSON, nullable=False)
    header_row = Column(Integer, default=1)
    data_start_row = Column(Integer, default=2)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_default = Column(Boolean, default=False)

    # Relationships
    user = relationship("User")

"""
Itinerary model — schedule items for a group/trip.
Each item represents an activity (flight, hotel, transport, event) on a specific date/time.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


class Itinerary(Base):
    """A single schedule item belonging to a group."""
    __tablename__ = "itineraries"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False, index=True)

    date = Column(String(20), nullable=False)       # YYYY-MM-DD
    time_start = Column(String(10), default="")      # HH:MM
    time_end = Column(String(10), default="")         # HH:MM
    activity = Column(String(500), nullable=False)    # What's happening
    location = Column(String(500), default="")        # Where
    notes = Column(Text, default="")                  # Extra details
    category = Column(String(50), default="activity") # flight | hotel | transport | activity | other

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    group = relationship("Group", backref="itineraries")

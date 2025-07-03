from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base

class UserActivityLog(Base):
    __tablename__ = "user_activity_log"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    activity_type = Column(String, index=True, nullable=False) # e.g., 'search', 'view_place', 'bookmark_place', 'create_review'
    place_id = Column(Integer, ForeignKey("places.id"), nullable=True) # Nullable if activity is not related to a specific place (e.g. general search)
    search_query = Column(String, nullable=True) # For 'search' activity type
    details = Column(String, nullable=True) # For any other relevant details, e.g., review_id for 'create_review'
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="activity_logs")
    place = relationship("Place", back_populates="activity_logs")

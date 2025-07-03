from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base

class Place(Base):
    __tablename__ = "places"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True)
    address = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    category = Column(String, index=True) # e.g., restaurant, temple, park
    tags = Column(JSON, nullable=True) # List of strings
    average_rating = Column(Float, default=0.0, nullable=False)
    review_count = Column(Integer, default=0, nullable=False) # Good to have for context
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    reviews = relationship("Review", back_populates="place")
    activity_logs = relationship("UserActivityLog", back_populates="place")

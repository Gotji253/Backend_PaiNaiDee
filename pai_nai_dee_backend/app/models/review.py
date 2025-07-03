from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base # Adjusted import path
from .user import User # Import User model
from .place import Place # Import Place model

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    rating = Column(Float, nullable=False) # e.g., 1.0 to 5.0
    comment = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    place_id = Column(Integer, ForeignKey("places.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    place = relationship("Place", back_populates="reviews")
    user = relationship("User", back_populates="reviews")


    def __repr__(self):
        return f"<Review(id={self.id}, place_id={self.place_id}, user_id={self.user_id}, rating={self.rating})>"

from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.sql import func # For server-side default timestamp
from sqlalchemy.orm import relationship

from app.db.base import Base

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    rating = Column(Float, nullable=False) # e.g., 1.0 to 5.0
    comment = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    place_id = Column(Integer, ForeignKey("places.id", ondelete="CASCADE"), nullable=False)
    place = relationship("Place", back_populates="reviews")

    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    owner = relationship("User", back_populates="reviews")

    def __repr__(self):
        return f"<Review(id={self.id}, place_id={self.place_id}, owner_id={self.owner_id}, rating={self.rating})>"

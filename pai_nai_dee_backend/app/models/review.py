from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func  # For default timestamp

from app.db.database import Base


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    rating = Column(Float, nullable=False)  # e.g., 1.0 to 5.0
    comment = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    place_id = Column(Integer, ForeignKey("places.id"), nullable=False)
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False
    )  # User who wrote the review

    # Relationships
    place = relationship("Place", back_populates="reviews")
    user = relationship("User", back_populates="reviews")

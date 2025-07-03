from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base # Adjusted import path
from .favorite import user_favorites # Import the association table


class Place(Base):
    __tablename__ = "places"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True)
    address = Column(String, nullable=True) # Added address
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    category = Column(String, index=True, nullable=True) # e.g., 'Restaurant', 'Temple', 'Viewpoint'

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Example of a foreign key to a user who submitted/owns the place
    # submitter_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    # submitter = relationship("User", back_populates="submitted_places")

    # Relationship to Reviews
    reviews = relationship("Review", back_populates="place", cascade="all, delete-orphan")

    # Relationship for favorites (many-to-many with users)
    favorited_by_users = relationship(
        "User",
        secondary=user_favorites,
        back_populates="favorite_places"
    )


    def __repr__(self):
        return f"<Place(id={self.id}, name='{self.name}')>"

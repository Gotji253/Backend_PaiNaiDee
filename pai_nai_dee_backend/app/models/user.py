from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship # Added relationship
from sqlalchemy.sql import func
from ..database import Base # Adjusted import path
from .favorite import user_favorites # Import the association table

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, index=True, nullable=True) # Optional full name
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False) # Optional superuser flag

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship to Reviews
    reviews = relationship("Review", back_populates="user", cascade="all, delete-orphan")

    # Relationship for submitted places (if you implement submitter_id in Place)
    # submitted_places = relationship("Place", back_populates="submitter", cascade="all, delete-orphan")

    # Relationship for favorites (many-to-many with Place)
    favorite_places = relationship(
        "Place",
        secondary=user_favorites,
        back_populates="favorited_by_users"
    )


    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"

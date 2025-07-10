from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship

from app.db.base import Base

class User(Base):
    __tablename__ = "users" # Explicitly setting tablename for clarity

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean(), default=True)
    is_superuser = Column(Boolean(), default=False) # Optional: for admin users

    # Relationships
    trips = relationship("Trip", back_populates="owner", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="owner", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"

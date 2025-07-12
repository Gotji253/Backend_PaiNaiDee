from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from ..db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=False)

    reviews = relationship("Review", back_populates="user")
    itineraries = relationship("Itinerary", back_populates="user")

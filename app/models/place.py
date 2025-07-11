from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base import Base


class Place(Base):
    __tablename__ = "places"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    address = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    category = Column(
        String, index=True, nullable=True
    )  # e.g., Restaurant, Landmark, Hotel

    # Relationships
    reviews = relationship(
        "Review", back_populates="place", cascade="all, delete-orphan"
    )
    # Association with Trip through an association table/object (many-to-many)
    # This will be defined in the Trip model or an association table model.

    def __repr__(self):
        return f"<Place(id={self.id}, name='{self.name}')>"

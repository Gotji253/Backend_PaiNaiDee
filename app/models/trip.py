from sqlalchemy import Column, Integer, String, Date, ForeignKey, Table
from sqlalchemy.orm import relationship

from app.db.base import Base

# Association table for the many-to-many relationship between Trip and Place
trip_place_association = Table(
    "trip_place_association",
    Base.metadata,
    Column("trip_id", Integer, ForeignKey("trips.id", ondelete="CASCADE"), primary_key=True),
    Column("place_id", Integer, ForeignKey("places.id", ondelete="CASCADE"), primary_key=True),
)

class Trip(Base):
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)

    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    owner = relationship("User", back_populates="trips")

    # Many-to-many relationship with Place
    places = relationship(
        "Place",
        secondary=trip_place_association,
        backref="trips" # Allows access from Place: place.trips
    )

    def __repr__(self):
        return f"<Trip(id={self.id}, name='{self.name}')>"

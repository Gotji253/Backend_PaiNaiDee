from sqlalchemy import Column, Integer, String, Float, ForeignKey, Table
from sqlalchemy.orm import relationship

# from sqlalchemy.dialects.postgresql import JSONB # If needed for complex types

from ..db.database import Base

# Association table for many-to-many relationship between itineraries and places
itinerary_place_association = Table(
    "itinerary_place_association",
    Base.metadata,
    Column("itinerary_id", Integer, ForeignKey("itineraries.id"), primary_key=True),
    Column("place_id", Integer, ForeignKey("places.id"), primary_key=True),
)


class Place(Base):
    __tablename__ = "places"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    category = Column(
        String, index=True, nullable=True
    )  # e.g., "Temple", "Market", "Restaurant"
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    address = Column(String, nullable=True)

    # Average rating - could be calculated or stored denormalized
    # For now, let's assume it's updated by a service layer when new reviews come in.
    average_rating = Column(Float, default=0.0, nullable=False)
    # To store things like opening hours, price range etc. a JSONB field could be useful.
    # details = Column(JSONB, nullable=True)

    # Relationships
    reviews = relationship(
        "Review", back_populates="place", cascade="all, delete-orphan"
    )

    # Itineraries that include this place (many-to-many)
    itineraries_featuring = relationship(
        "Itinerary",
        secondary=itinerary_place_association,
        back_populates="places_in_itinerary",
    )

    # If we implement a "bookmarks" feature:
    # bookmarked_by_users = relationship("User", secondary="user_bookmarks_place", back_populates="bookmarked_places")


# If we implement user bookmarks (many-to-many between User and Place)
# user_bookmarks_place = Table(
#     'user_bookmarks_place', Base.metadata,
#     Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
#     Column('place_id', Integer, ForeignKey('places.id'), primary_key=True)
# )
